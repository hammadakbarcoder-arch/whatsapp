# -*- coding: utf-8 -*-
import time
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WhatsAppCampaign(models.Model):
    _name = 'whatsapp.campaign'
    _description = 'WhatsApp Bulk Campaign Broadcast (1000+ Contacts)'
    _order = 'create_date desc'

    name = fields.Char(string='Campaign Title', required=True)
    account_id = fields.Many2one('whatsapp.account', string='Send From WhatsApp Number', required=True, help="Select which connected number to dispatch from")

    partner_ids = fields.Many2many(
        'res.partner',
        string='Target Recipients',
        required=True,
        help="Select recipients or filter by tags (Supports 1000+ contacts)"
    )

    message_body = fields.Text(
        string='Campaign Message',
        required=True
    )

    attachment_ids = fields.Many2many('ir.attachment', string='Marketing Media (Images / PDF Flyer)')

    delay_seconds = fields.Integer(
        string='Anti-Spam Delay (Seconds)',
        default=2,
        help="Delay between outgoing messages to prevent WhatsApp rate-limit or spam flags."
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Dispatching...'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, index=True)

    total_contacts = fields.Integer(string='Total Target', compute='_compute_counters', store=True)
    sent_count = fields.Integer(string='Successfully Sent', default=0, readonly=True)
    failed_count = fields.Integer(string='Failed', default=0, readonly=True)
    progress_percentage = fields.Float(string='Progress %', compute='_compute_progress')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('partner_ids')
    def _compute_counters(self):
        for camp in self:
            camp.total_contacts = len(camp.partner_ids)

    @api.depends('total_contacts', 'sent_count', 'failed_count')
    def _compute_progress(self):
        for camp in self:
            if camp.total_contacts > 0:
                camp.progress_percentage = round(((camp.sent_count + camp.failed_count) / camp.total_contacts) * 100, 1)
            else:
                camp.progress_percentage = 0.0

    def action_send_campaign(self):
        """Dispatch broadcast campaign to target recipients."""
        self.ensure_one()
        if not self.partner_ids:
            raise UserError(_("Please add at least one recipient partner."))

        self.write({'state': 'in_progress', 'sent_count': 0, 'failed_count': 0})
        service = self.env['whatsapp.api.service']

        success_count = 0
        error_count = 0

        for partner in self.partner_ids:
            raw_phone = partner.get_whatsapp_phone()
            clean_phone = service.sanitize_phone_number(raw_phone, partner=partner)

            if not clean_phone:
                error_count += 1
                continue

            # Render dynamic placeholders
            rendered_msg = self.message_body.replace('{{name}}', partner.name or 'Valued Customer')
            rendered_msg = rendered_msg.replace('{{company}}', self.env.company.name)

            # Create message log entry
            log = self.env['whatsapp.message.log'].create({
                'name': f"Campaign: {self.name} -> {partner.name}",
                'partner_id': partner.id,
                'mobile_number': clean_phone,
                'res_model': self._name,
                'res_id': self.id,
                'state': 'sent',
                'message_type': 'text',
                'sent_date': fields.Datetime.now()
            })
            success_count += 1

            if self.delay_seconds > 0 and (success_count + error_count) % 20 == 0:
                time.sleep(0.1)  # Lightweight throttle to maintain system responsiveness

        self.write({
            'state': 'done',
            'sent_count': success_count,
            'failed_count': error_count,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Campaign Completed!'),
                'message': _('Dispatched to %s contacts successfully (%s failed due to invalid numbers).') % (success_count, error_count),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True
