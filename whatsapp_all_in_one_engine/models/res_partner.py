# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    whatsapp_message_count = fields.Integer(
        string='WhatsApp Messages',
        compute='_compute_whatsapp_counts'
    )
    whatsapp_call_count = fields.Integer(
        string='WhatsApp Calls',
        compute='_compute_whatsapp_counts'
    )

    def _compute_whatsapp_counts(self):
        log_obj = self.env['whatsapp.message.log']
        call_obj = self.env['whatsapp.call.log']
        for partner in self:
            partner.whatsapp_message_count = log_obj.search_count([('partner_id', '=', partner.id)])
            partner.whatsapp_call_count = call_obj.search_count([('partner_id', '=', partner.id)])

    def get_whatsapp_phone(self):
        """Safely retrieve mobile or phone without attribute errors."""
        self.ensure_one()
        return getattr(self, 'mobile', False) or getattr(self, 'phone', False) or ''

    def action_view_whatsapp_logs(self):
        """View all WhatsApp messages sent to this partner."""
        self.ensure_one()
        return {
            'name': _('WhatsApp History - %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.message.log',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_whatsapp_calls(self):
        """View all WhatsApp calls logged for this partner."""
        self.ensure_one()
        return {
            'name': _('WhatsApp Calls - %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.call.log',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_log_whatsapp_call(self):
        """Open form to log a new call."""
        self.ensure_one()
        return {
            'name': _('Log WhatsApp Call - %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.call.log',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
            }
        }

    def action_send_whatsapp(self):
        """Open interactive WhatsApp Composer for this contact."""
        self.ensure_one()
        template = self.env['whatsapp.template'].search([('model', '=', 'res.partner')], limit=1)
        raw_phone = self.get_whatsapp_phone()
        clean_phone = self.env['whatsapp.api.service'].sanitize_phone_number(raw_phone, partner=self)

        return {
            'name': _('Send WhatsApp Message'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.composer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_mobile_number': clean_phone or raw_phone,
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_template_id': template.id if template else False,
            }
        }
