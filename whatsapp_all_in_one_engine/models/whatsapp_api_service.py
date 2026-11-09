# -*- coding: utf-8 -*-
import json
import logging
import re
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WhatsAppApiService(models.AbstractModel):
    _name = 'whatsapp.api.service'
    _description = 'Meta WhatsApp Cloud API Connector Engine'

    @api.model
    def sanitize_phone_number(self, phone, partner=None):
        """
        Sanitize phone number to strict E.164 digits format (without '+').
        Supports automatic country code resolution if leading 0 is detected.
        """
        if not phone:
            return False

        # Remove all spaces, dashes, brackets, and '+'
        clean = re.sub(r'[\s\-\(\)\+]', '', str(phone).strip())

        # If starts with leading zero (e.g. 03001234567 in Pakistan)
        if clean.startswith('0'):
            country = partner.country_id if partner and partner.country_id else self.env.company.country_id
            if country and country.phone_code:
                clean = f"{country.phone_code}{clean.lstrip('0')}"

        # Clean non-digits
        clean = re.sub(r'\D', '', clean)
        return clean if len(clean) >= 7 else False

    @api.model
    def _get_api_credentials(self):
        """Retrieve Meta Cloud API configuration."""
        ICP = self.env['ir.config_parameter'].sudo()
        base_url = ICP.get_param('whatsapp_all_in_one_engine.api_url', 'https://graph.facebook.com')
        version = ICP.get_param('whatsapp_all_in_one_engine.api_version', 'v21.0')
        phone_id = ICP.get_param('whatsapp_all_in_one_engine.phone_number_id')
        token = ICP.get_param('whatsapp_all_in_one_engine.access_token')

        if not phone_id or not token:
            _logger.warning("WhatsApp Meta Cloud API is not configured. Missing Phone ID or Access Token.")
            return None

        return {
            'base_url': base_url.rstrip('/'),
            'version': version,
            'phone_id': phone_id,
            'token': token,
            'messages_endpoint': f"{base_url.rstrip('/')}/{version}/{phone_id}/messages",
            'media_endpoint': f"{base_url.rstrip('/')}/{version}/{phone_id}/media",
        }

    @api.model
    def upload_media_document(self, pdf_content, filename):
        """
        Uploads PDF to Meta Media API and returns media_id.
        This works reliably even on localhost without requiring a public URL!
        """
        creds = self._get_api_credentials()
        if not creds:
            raise UserError(_("Meta WhatsApp Cloud API is not configured."))

        headers = {
            'Authorization': f"Bearer {creds['token']}",
        }
        files = {
            'file': (filename, pdf_content, 'application/pdf'),
        }
        data = {
            'messaging_product': 'whatsapp',
            'type': 'application/pdf',
        }

        try:
            response = requests.post(
                creds['media_endpoint'],
                headers=headers,
                data=data,
                files=files,
                timeout=25
            )
            if response.status_code in (200, 201):
                res_data = response.json()
                return res_data.get('id')
            else:
                _logger.error("Meta Media Upload Failed [%s]: %s", response.status_code, response.text)
                return None
        except Exception as e:
            _logger.error("Exception uploading media to Meta: %s", str(e))
            return None

    @api.model
    def send_template_message(self, record, template, recipient_number=None, custom_pdf=None, custom_filename=None, log_id=None):
        """
        Main engine method: renders template, uploads PDF (if any), and calls Meta Cloud API.
        """
        creds = self._get_api_credentials()
        if not creds:
            _logger.warning("WhatsApp API cannot send: missing credentials.")
            return False

        # Determine Partner and Phone
        partner = getattr(record, 'partner_id', None)
        if hasattr(record, '_name') and record._name == 'res.partner':
            partner = record

        raw_phone = recipient_number or (partner.get_whatsapp_phone() if partner and hasattr(partner, 'get_whatsapp_phone') else (getattr(partner, 'phone', None) or getattr(partner, 'mobile', None)) if partner else None)
        clean_phone = self.sanitize_phone_number(raw_phone, partner=partner)

        if not clean_phone:
            err_msg = _("Invalid or missing phone number for record %s") % record.display_name
            _logger.warning(err_msg)
            if log_id:
                log_id.write({'state': 'failed', 'error_message': err_msg})
            else:
                self.env['whatsapp.message.log'].create({
                    'name': f"Failed: {record.display_name}",
                    'partner_id': partner.id if partner else False,
                    'mobile_number': str(raw_phone or 'N/A'),
                    'res_model': record._name,
                    'res_id': record.id,
                    'state': 'failed',
                    'error_message': err_msg,
                })
            return False

        # Create or update Log entry
        if not log_id:
            log_id = self.env['whatsapp.message.log'].create({
                'name': f"{template.name} - {record.display_name}",
                'partner_id': partner.id if partner else False,
                'mobile_number': clean_phone,
                'template_id': template.id,
                'res_model': record._name,
                'res_id': record.id,
                'state': 'draft',
            })

        components = []

        # Header Component (PDF Document or Text)
        media_id = None
        pdf_bytes = custom_pdf
        filename = custom_filename

        if template.header_type == 'document':
            if not pdf_bytes:
                pdf_bytes, filename = template.render_document_attachment(record)

            if pdf_bytes:
                # Save attachment for historical reference in Odoo
                try:
                    att = self.env['ir.attachment'].create({
                        'name': filename or 'document.pdf',
                        'type': 'binary',
                        'raw': pdf_bytes,
                        'res_model': log_id._name,
                        'res_id': log_id.id,
                        'mimetype': 'application/pdf',
                    })
                    log_id.write({'attachment_id': att.id, 'attachment_filename': filename})
                except Exception as ex:
                    _logger.warning("Could not save ir.attachment: %s", ex)

                # Upload to Meta Cloud API Media Endpoint
                media_id = self.upload_media_document(pdf_bytes, filename)
                if media_id:
                    components.append({
                        'type': 'header',
                        'parameters': [
                            {
                                'type': 'document',
                                'document': {
                                    'id': media_id,
                                    'filename': filename or 'document.pdf',
                                }
                            }
                        ]
                    })
                else:
                    _logger.warning("Could not obtain media_id from Meta API for %s", filename)

        elif template.header_type == 'text' and template.header_text:
            components.append({
                'type': 'header',
                'parameters': [
                    {'type': 'text', 'text': template.header_text}
                ]
            })

        # Body Component (Dynamic Variables)
        body_params = template.render_body_parameters(record)
        if body_params:
            components.append({
                'type': 'body',
                'parameters': body_params
            })

        # Build Final Payload
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': clean_phone,
            'type': 'template',
            'template': {
                'name': template.template_name,
                'language': {'code': template.language_code},
                'components': components
            }
        }

        headers = {
            'Authorization': f"Bearer {creds['token']}",
            'Content-Type': 'application/json'
        }

        log_id.write({
            'payload_sent': json.dumps(payload, indent=2),
            'attachment_filename': filename or False,
        })

        try:
            response = requests.post(
                creds['messages_endpoint'],
                headers=headers,
                data=json.dumps(payload),
                timeout=20
            )

            res_text = response.text
            log_id.write({'response_received': res_text})

            if response.status_code in (200, 201):
                res_json = response.json()
                messages = res_json.get('messages', [])
                wamid = messages[0].get('id') if messages else False

                log_id.write({
                    'state': 'sent',
                    'meta_message_id': wamid,
                    'error_message': False,
                    'sent_date': fields.Datetime.now()
                })
                _logger.info("WhatsApp successfully sent for %s (WAMID: %s)", record.display_name, wamid)
                return True
            else:
                err_json = response.json().get('error', {})
                err_msg = err_json.get('message', res_text)
                log_id.write({
                    'state': 'failed',
                    'error_message': f"Meta API Error ({response.status_code}): {err_msg}"
                })
                _logger.error("Failed to send WhatsApp message: %s", err_msg)
                return False

        except requests.exceptions.RequestException as e:
            err_msg = f"Network Connection Error: {str(e)}"
            log_id.write({'state': 'failed', 'error_message': err_msg})
            _logger.error(err_msg)
            return False
