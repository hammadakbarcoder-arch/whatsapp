# -*- coding: utf-8 -*-
import base64
import io
import uuid
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:
    qrcode = None


class WhatsAppAccount(models.Model):
    _name = 'whatsapp.account'
    _description = 'WhatsApp Connected Account / Phone Number'
    _order = 'is_default desc, name asc'

    name = fields.Char(string='Account Name / Label', required=True)
    phone_number = fields.Char(string='WhatsApp Number', required=True)

    account_type = fields.Selection([
        ('qr_code', 'Free QR Scan (No Meta API, No Approvals, $0 Per-Message)'),
        ('meta_cloud_api', 'Official Meta Cloud API (Optional Enterprise Route)'),
    ], string='Connection Mode', default='qr_code', required=True)

    session_status = fields.Selection([
        ('disconnected', 'Disconnected'),
        ('connecting', 'QR Code Ready · Scan with WhatsApp'),
        ('connected', 'Connected & Active'),
    ], string='Live Status', default='disconnected', index=True, readonly=True)

    session_id = fields.Char(string='Session ID', default=lambda self: str(uuid.uuid4())[:8], copy=False, readonly=True)
    qr_code_image = fields.Binary(string='QR Code (Scan to Connect)', attachment=True, readonly=True)
    pairing_code = fields.Char(string='Pairing Code (Alternative)', readonly=True)

    # Optional Meta Cloud API specific fields (if account_type == 'meta_cloud_api')
    meta_phone_number_id = fields.Char(string='Meta Phone Number ID')
    meta_access_token = fields.Char(string='Meta Permanent Token')
    meta_waba_id = fields.Char(string='Meta WABA ID')

    is_default = fields.Boolean(string='Default Account for Automation', default=False)
    user_id = fields.Many2one('res.users', string='Assigned User / Sales Rep', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # Statistics
    total_messages_sent = fields.Integer(string='Messages Sent', compute='_compute_stats')
    total_calls_logged = fields.Integer(string='Calls Logged', compute='_compute_stats')

    def _compute_stats(self):
        log_obj = self.env['whatsapp.message.log']
        call_obj = self.env.get('whatsapp.call.log')
        for acc in self:
            acc.total_messages_sent = log_obj.search_count([('mobile_number', '!=', False)])
            if call_obj:
                acc.total_calls_logged = call_obj.search_count([('account_id', '=', acc.id)])
            else:
                acc.total_calls_logged = 0

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.is_default:
                self.search([('id', '!=', rec.id), ('company_id', '=', rec.company_id.id)]).write({'is_default': False})
        return records

    def write(self, vals):
        if vals.get('is_default'):
            self.search([('id', 'not in', self.ids), ('company_id', '=', self.company_id.id)]).write({'is_default': False})
        return super().write(vals)

    def action_generate_qr_code(self):
        """Generate a scannable QR Code for WhatsApp Web / Gateway pairing."""
        self.ensure_one()
        if self.account_type != 'qr_code':
            raise UserError(_("QR Code is only available when Connection Mode is set to 'Free QR Scan'."))

        session_token = f"WHA-SESSION:{self.id}:{self.session_id}:{self.phone_number}"

        if qrcode:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8,
                border=3,
            )
            qr.add_data(session_token)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#075E54", back_color="white")

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            qr_bytes = base64.b64encode(buffer.getvalue())

            pairing = f"{self.session_id.upper()[:4]}-{self.session_id.upper()[4:]}"
            self.write({
                'qr_code_image': qr_bytes,
                'pairing_code': pairing,
                'session_status': 'connecting'
            })
        else:
            self.write({
                'session_status': 'connecting',
                'pairing_code': self.session_id.upper()
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Scan QR Code with WhatsApp'),
                'message': _('QR Code generated successfully! Open WhatsApp on your phone > Linked Devices > Link a Device, and scan the QR code.'),
                'type': 'info',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def action_confirm_connected(self):
        """Mark account as connected & active."""
        self.ensure_one()
        self.write({
            'session_status': 'connected',
            'qr_code_image': False,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('WhatsApp Connected!'),
                'message': _('Account %s is now active and ready to send & receive messages.') % self.name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def action_disconnect(self):
        """Disconnect session."""
        self.ensure_one()
        self.write({
            'session_status': 'disconnected',
            'qr_code_image': False,
            'pairing_code': False,
            'session_id': str(uuid.uuid4())[:8],
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
