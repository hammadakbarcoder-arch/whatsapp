# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class WhatsAppMessageLog(models.Model):
    _name = 'whatsapp.message.log'
    _description = 'WhatsApp Message Audit & Delivery Log'
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Reference', required=True, default=lambda self: _('New Message'))
    partner_id = fields.Many2one('res.partner', string='Recipient Customer', index=True)
    mobile_number = fields.Char(string='Mobile Number (E.164)', required=True, index=True)

    template_id = fields.Many2one('whatsapp.template', string='Template Used')
    res_model = fields.Char(string='Related Model', index=True)
    res_id = fields.Integer(string='Related Record ID', index=True)
    record_ref = fields.Char(string='Document Ref', compute='_compute_record_ref', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to Meta'),
        ('delivered', 'Delivered to Customer'),
        ('read', 'Read by Customer'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', index=True)

    message_type = fields.Selection([
        ('template', 'Official Template'),
        ('document', 'Document / PDF'),
        ('text', 'Direct Message'),
    ], string='Message Type', default='template')

    attachment_filename = fields.Char(string='Attached PDF / File')
    attachment_id = fields.Many2one('ir.attachment', string='Stored Attachment')

    meta_message_id = fields.Char(string='Meta WAMID', help='Official WhatsApp Message ID from Meta response')
    error_message = fields.Text(string='Error Trace / Details')
    payload_sent = fields.Text(string='Raw Payload Sent')
    response_received = fields.Text(string='Raw API Response')

    sent_date = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('res_model', 'res_id')
    def _compute_record_ref(self):
        for log in self:
            if log.res_model and log.res_id:
                try:
                    record = self.env[log.res_model].browse(log.res_id)
                    log.record_ref = record.display_name if record.exists() else f"{log.res_model},{log.res_id}"
                except Exception:
                    log.record_ref = f"{log.res_model},{log.res_id}"
            else:
                log.record_ref = False

    def action_open_record(self):
        """Open the related document."""
        self.ensure_one()
        if not self.res_model or not self.res_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_retry(self):
        """Retry sending a failed message."""
        self.ensure_one()
        if not self.res_model or not self.res_id or not self.template_id:
            return False
        record = self.env[self.res_model].browse(self.res_id)
        if not record.exists():
            return False
        service = self.env['whatsapp.api.service']
        return service.send_template_message(
            record=record,
            template=self.template_id,
            recipient_number=self.mobile_number,
            log_id=self
        )
