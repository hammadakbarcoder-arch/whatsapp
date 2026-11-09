# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Meta Cloud API Credentials
    whatsapp_api_url = fields.Char(
        string='Meta API Base URL',
        default='https://graph.facebook.com',
        config_parameter='whatsapp_all_in_one_engine.api_url',
        help='Official Meta Graph API URL (default: https://graph.facebook.com)'
    )
    whatsapp_api_version = fields.Char(
        string='API Version',
        default='v21.0',
        config_parameter='whatsapp_all_in_one_engine.api_version',
        help='Meta Graph API version (e.g. v21.0)'
    )
    whatsapp_phone_number_id = fields.Char(
        string='Phone Number ID',
        config_parameter='whatsapp_all_in_one_engine.phone_number_id',
        help='Your WhatsApp Business Phone Number ID from Meta Developer Portal'
    )
    whatsapp_business_account_id = fields.Char(
        string='WABA ID (Business Account ID)',
        config_parameter='whatsapp_all_in_one_engine.waba_id',
        help='Your WhatsApp Business Account (WABA) ID'
    )
    whatsapp_access_token = fields.Char(
        string='Permanent Access Token',
        config_parameter='whatsapp_all_in_one_engine.access_token',
        help='System User Access Token with whatsapp_business_messaging permissions'
    )
    whatsapp_webhook_token = fields.Char(
        string='Webhook Verify Token',
        config_parameter='whatsapp_all_in_one_engine.webhook_token',
        help='Secret verification token for incoming delivery receipts'
    )

    # Automated Workflow Toggles & Template Links
    whatsapp_auto_sale = fields.Boolean(
        string='Auto-Send on Sales Confirmation',
        config_parameter='whatsapp_all_in_one_engine.auto_sale',
        help='Automatically send WhatsApp message and Sales Order PDF when confirmed'
    )
    whatsapp_sale_template_id = fields.Many2one(
        'whatsapp.template',
        string='Sales Order Template',
        config_parameter='whatsapp_all_in_one_engine.sale_template_id',
        domain=[('model', '=', 'sale.order')],
        help='Meta-approved template to use when Sales Order is confirmed'
    )

    whatsapp_auto_invoice = fields.Boolean(
        string='Auto-Send on Invoice Post',
        config_parameter='whatsapp_all_in_one_engine.auto_invoice',
        help='Automatically send WhatsApp message and Invoice PDF when posted/validated'
    )
    whatsapp_invoice_template_id = fields.Many2one(
        'whatsapp.template',
        string='Customer Invoice Template',
        config_parameter='whatsapp_all_in_one_engine.invoice_template_id',
        domain=[('model', '=', 'account.move')],
        help='Meta-approved template to use when Customer Invoice is posted'
    )

    whatsapp_auto_delivery = fields.Boolean(
        string='Auto-Send on Delivery Done',
        config_parameter='whatsapp_all_in_one_engine.auto_delivery',
        help='Automatically send WhatsApp message and Delivery Slip PDF when dispatch is validated'
    )
    whatsapp_delivery_template_id = fields.Many2one(
        'whatsapp.template',
        string='Delivery Order Template',
        config_parameter='whatsapp_all_in_one_engine.delivery_template_id',
        domain=[('model', '=', 'stock.picking')],
        help='Meta-approved template to use when Delivery is validated'
    )

    def action_test_whatsapp_connection(self):
        """Test Meta WhatsApp Cloud API credentials."""
        self.ensure_one()
        phone_id = self.whatsapp_phone_number_id or self.env['ir.config_parameter'].sudo().get_param('whatsapp_all_in_one_engine.phone_number_id')
        token = self.whatsapp_access_token or self.env['ir.config_parameter'].sudo().get_param('whatsapp_all_in_one_engine.access_token')
        version = self.whatsapp_api_version or self.env['ir.config_parameter'].sudo().get_param('whatsapp_all_in_one_engine.api_version', 'v21.0')
        base_url = self.whatsapp_api_url or self.env['ir.config_parameter'].sudo().get_param('whatsapp_all_in_one_engine.api_url', 'https://graph.facebook.com')

        if not phone_id or not token:
            raise UserError(_("Please provide both Phone Number ID and Access Token to test connection."))

        endpoint = f"{base_url.rstrip('/')}/{version}/{phone_id}"
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                verified_name = data.get('verified_name', data.get('display_phone_number', 'Connected Phone'))
                quality = data.get('quality_rating', 'N/A')
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Successful!'),
                        'message': _('Successfully connected to Meta WhatsApp API!\nPhone: %s | Quality Rating: %s') % (verified_name, quality),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                err_data = response.json().get('error', {})
                err_msg = err_data.get('message', response.text)
                raise UserError(_("Meta API Error (%s):\n%s") % (response.status_code, err_msg))
        except requests.exceptions.RequestException as e:
            raise UserError(_("Failed to connect to Meta API: %s") % str(e))
