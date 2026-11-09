# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    whatsapp_status = fields.Selection([
        ('not_sent', 'Not Sent'),
        ('sent', 'Sent to WhatsApp'),
        ('failed', 'Sending Failed')
    ], string='WhatsApp Status', default='not_sent', copy=False, readonly=True)

    def action_confirm(self):
        """Override to auto-send WhatsApp on Sales Order confirmation."""
        res = super(SaleOrder, self).action_confirm()

        ICP = self.env['ir.config_parameter'].sudo()
        auto_send = ICP.get_param('whatsapp_all_in_one_engine.auto_sale', False)

        if auto_send:
            for order in self:
                order._send_whatsapp_sales_notification()

        return res

    def _send_whatsapp_sales_notification(self):
        """Helper method to send WhatsApp for confirmed sale order."""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        template_id = ICP.get_param('whatsapp_all_in_one_engine.sale_template_id')
        template = False
        if template_id:
            template = self.env['whatsapp.template'].browse(int(template_id))
        if not template or not template.exists():
            template = self.env['whatsapp.template'].search([('model', '=', 'sale.order')], limit=1)

        if not template:
            _logger.info("No active WhatsApp template found for sale.order")
            return False

        service = self.env['whatsapp.api.service']
        success = service.send_template_message(record=self, template=template)
        if success:
            self.write({'whatsapp_status': 'sent'})
        else:
            self.write({'whatsapp_status': 'failed'})
        return success

    def action_send_whatsapp(self):
        """Open interactive WhatsApp Composer for this Sales Order."""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        template_id = ICP.get_param('whatsapp_all_in_one_engine.sale_template_id')
        template = self.env['whatsapp.template'].browse(int(template_id)) if template_id else False
        if not template or not template.exists():
            template = self.env['whatsapp.template'].search([('model', '=', 'sale.order')], limit=1)

        phone = self.partner_id.get_whatsapp_phone() if self.partner_id else ''
        clean_phone = self.env['whatsapp.api.service'].sanitize_phone_number(phone, partner=self.partner_id)

        # Generate PDF preview
        pdf_content = False
        filename = f"{self.name}.pdf".replace('/', '_')
        if template and template.header_type == 'document' and template.report_id:
            pdf_content, filename = template.render_document_attachment(self)

        return {
            'name': _('Send Sales Order via WhatsApp'),
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
