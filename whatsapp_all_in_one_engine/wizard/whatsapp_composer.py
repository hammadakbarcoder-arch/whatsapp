# -*- coding: utf-8 -*-
import logging
import urllib.parse
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WhatsAppComposer(models.TransientModel):
    _name = 'whatsapp.composer'
    _description = 'Interactive WhatsApp Message Composer'

    account_id = fields.Many2one(
        'whatsapp.account',
        string='Send From WhatsApp Number',
        default=lambda self: self.env['whatsapp.account'].search([('is_default', '=', True)], limit=1) or self.env['whatsapp.account'].search([], limit=1),
        help="Select which connected WhatsApp account/number to dispatch from"
    )
    partner_id = fields.Many2one('res.partner', string='Recipient', required=True)
    mobile_number = fields.Char(string='Mobile Phone (E.164)', required=True)
    res_model = fields.Char(string='Related Model')
    res_id = fields.Integer(string='Related Record ID')

    template_id = fields.Many2one(
        'whatsapp.template',
        string='Template (Optional for QR Mode)',
        domain="[('model', '=', res_model)]"
    )
    message_body = fields.Text(string='Message Content / Preview', compute='_compute_message_body', readonly=False, store=True)

    attachment_filename = fields.Char(string='PDF Attachment Name')
    attachment_ids = fields.Many2many('ir.attachment', string='Extra Attachments')

    send_mode = fields.Selection([
        ('direct_dispatch', 'Direct WhatsApp Dispatch (QR / Meta API)'),
        ('whatsapp_web', 'Open in WhatsApp Web / Desktop App (Manual Send)'),
    ], string='Dispatch Channel', default='direct_dispatch', required=True)

    @api.depends('template_id', 'res_model', 'res_id')
    def _compute_message_body(self):
        for comp in self:
            if comp.template_id and comp.res_model and comp.res_id:
                try:
                    record = self.env[comp.res_model].browse(comp.res_id)
                    rendered = comp.template_id.body_text or ''
                    for var in comp.template_id.variable_ids:
                        val = var.get_value(record)
                        rendered = rendered.replace(f"{{{{{var.sequence}}}}}", str(val or ''))
                    comp.message_body = rendered
                except Exception as e:
                    _logger.warning("Error computing composer preview: %s", e)
                    comp.message_body = comp.template_id.body_text
            elif not comp.message_body:
                comp.message_body = ''

    def action_send(self):
        """Send the WhatsApp message via QR / Meta Cloud API or WhatsApp Web."""
        self.ensure_one()

        clean_number = self.env['whatsapp.api.service'].sanitize_phone_number(
            self.mobile_number, partner=self.partner_id
        )
        if not clean_number:
            raise UserError(_("Please provide a valid recipient mobile phone number."))

        if self.send_mode == 'direct_dispatch':
            record = False
            if self.res_model and self.res_id:
                record = self.env[self.res_model].browse(self.res_id)

            if not record or not record.exists():
                record = self.partner_id

            # Create message log
            log = self.env['whatsapp.message.log'].create({
                'name': f"Message to {self.partner_id.name}",
                'partner_id': self.partner_id.id,
                'mobile_number': clean_number,
                'res_model': record._name if record else False,
                'res_id': record.id if record else False,
                'template_id': self.template_id.id if self.template_id else False,
                'attachment_filename': self.attachment_filename or False,
                'state': 'sent',
                'sent_date': fields.Datetime.now()
            })

            # If template exists, call service
            if self.template_id:
                service = self.env['whatsapp.api.service']
                service.send_template_message(
                    record=record,
                    template=self.template_id,
                    recipient_number=clean_number,
                    log_id=log
                )

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('WhatsApp Dispatched!'),
                    'message': _('Message successfully sent to %s.') % clean_number,
                    'type': 'success',
                    'sticky': False,
                }
            }

        elif self.send_mode == 'whatsapp_web':
            text = urllib.parse.quote(self.message_body or '')
            url = f"https://wa.me/{clean_number}?text={text}"
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
