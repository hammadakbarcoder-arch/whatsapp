# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class WhatsAppCallLog(models.Model):
    _name = 'whatsapp.call.log'
    _description = 'WhatsApp Voice & Video Call Log (Customer-360)'
    _order = 'call_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Call Subject', required=True, default=lambda self: _('WhatsApp Call'))
    partner_id = fields.Many2one('res.partner', string='Customer / Contact', required=True, index=True)
    account_id = fields.Many2one('whatsapp.account', string='WhatsApp Number Used')

    call_type = fields.Selection([
        ('voice', 'WhatsApp Voice Call'),
        ('video', 'WhatsApp Video Call'),
        ('meeting', 'Group / Team Meeting'),
    ], string='Call Type', default='voice', required=True)

    call_status = fields.Selection([
        ('completed', 'Connected & Answered'),
        ('missed', 'Missed Call'),
        ('rejected', 'Declined / Busy'),
    ], string='Call Outcome', default='completed', required=True)

    duration_minutes = fields.Float(string='Duration (Minutes)', default=1.0)
    summary = fields.Text(string='Call Notes & Action Items')

    call_date = fields.Datetime(string='Call Time', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Agent / Sales Rep', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
