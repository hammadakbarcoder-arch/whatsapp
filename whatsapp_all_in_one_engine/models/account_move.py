# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    whatsapp_status = fields.Selection([
        ('not_sent', 'Not Sent'),
        ('sent', 'Sent to WhatsApp'),
        ('failed', 'Sending Failed')
    ], string='WhatsApp Status', default='not_sent', copy=False, readonly=True)

    def action_post(self):
        """Override to auto-send WhatsApp on Customer Invoice validation."""
        res = super(AccountMove, self).action_post()

        ICP = self.env['ir.config_parameter'].sudo()
        auto_send = ICP.get_param('whatsapp_all_in_one_engine.auto_invoice', False)

        if auto_send:
            for move in self:
                if move.is_sale_document(include_receipts=True):
                    move._send_whatsapp_invoice_notification()

        return res

    def _send_whatsapp_invoice_notification(self):
        """Helper to send WhatsApp message and Invoice PDF."""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        template_id = ICP.get_param('whatsapp_all_in_one_engine.invoice_template_id')
        template = False
        if template_id:
            template = self.env['whatsapp.template'].browse(int(template_id))
        if not template or not template.exists():
            template = self.env['whatsapp.template'].search([('model', '=', 'account.move')], limit=1)

        if not template:
            _logger.info("No active WhatsApp template found for account.move")
            return False

        service = self.env['whatsapp.api.service']
        success = service.send_template_message(record=self, template=template)
        if success:
            self.write({'whatsapp_status': 'sent'})
        else:
            self.write({'whatsapp_status': 'failed'})
        return success

    def action_send_whatsapp(self):
        """Open interactive WhatsApp Composer for this Invoice."""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        template_id = ICP.get_param('whatsapp_all_in_one_engine.invoice_template_id')
        template = self.env['whatsapp.template'].browse(int(template_id)) if template_id else False
        if not template or not template.exists():
            template = self.env['whatsapp.template'].search([('model', '=', 'account.move')], limit=1)

        phone = self.partner_id.get_whatsapp_phone() if self.partner_id else ''
        clean_phone = self.env['whatsapp.api.service'].sanitize_phone_number(phone, partner=self.partner_id)

        filename = f"{self.name or 'Invoice'}.pdf".replace('/', '_')

        return {
            'name': _('Send Invoice via WhatsApp'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.composer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_mobile_number': clean_phone or phone,
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_template_id': template.id if template else False,
                'default_attachment_filename': filename,
            }
        }
