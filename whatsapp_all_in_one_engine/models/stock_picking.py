# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    whatsapp_status = fields.Selection([
        ('not_sent', 'Not Sent'),
        ('sent', 'Sent to WhatsApp'),
        ('failed', 'Sending Failed')
    ], string='WhatsApp Status', default='not_sent', copy=False, readonly=True)

    def _action_done(self):
        """Override to auto-send WhatsApp on Outgoing Delivery validation."""
        res = super(StockPicking, self)._action_done()

        ICP = self.env['ir.config_parameter'].sudo()
        auto_send = ICP.get_param('whatsapp_all_in_one_engine.auto_delivery', False)

        if auto_send:
            for picking in self:
                if picking.picking_type_code == 'outgoing' and picking.partner_id:
                    picking._send_whatsapp_delivery_notification()

        return res

    def _send_whatsapp_delivery_notification(self):
        """Helper to send WhatsApp message and Delivery Slip PDF."""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        template_id = ICP.get_param('whatsapp_all_in_one_engine.delivery_template_id')
        template = False
        if template_id:
            template = self.env['whatsapp.template'].browse(int(template_id))
        if not template or not template.exists():
            template = self.env['whatsapp.template'].search([('model', '=', 'stock.picking')], limit=1)

        if not template:
            _logger.info("No active WhatsApp template found for stock.picking")
            return False

        service = self.env['whatsapp.api.service']
        success = service.send_template_message(record=self, template=template)
        if success:
            self.write({'whatsapp_status': 'sent'})
        else:
            self.write({'whatsapp_status': 'failed'})
        return success

    def action_send_whatsapp(self):
        """Open interactive WhatsApp Composer for this Delivery."""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        template_id = ICP.get_param('whatsapp_all_in_one_engine.delivery_template_id')
        template = self.env['whatsapp.template'].browse(int(template_id)) if template_id else False
        if not template or not template.exists():
            template = self.env['whatsapp.template'].search([('model', '=', 'stock.picking')], limit=1)

        phone = self.partner_id.get_whatsapp_phone() if self.partner_id else ''
        clean_phone = self.env['whatsapp.api.service'].sanitize_phone_number(phone, partner=self.partner_id)

        filename = f"{self.name or 'Delivery'}.pdf".replace('/', '_')

        return {
            'name': _('Send Delivery Slip via WhatsApp'),
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
