# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WhatsAppTemplate(models.Model):
    _name = 'whatsapp.template'
    _description = 'WhatsApp Meta Cloud API Template'
    _order = 'name asc'

    name = fields.Char(string='Template Title', required=True, translate=True)
    template_name = fields.Char(
        string='Meta Template Name',
        required=True,
        help='Exact template name approved in Meta WhatsApp Manager (lowercase, underscore separated, e.g. sales_order_confirm)'
    )
    language_code = fields.Char(
        string='Language Code',
        default='en_US',
        required=True,
        help='e.g. en_US, ar, ur, es, fr'
    )
    category = fields.Selection([
        ('UTILITY', 'Utility (Transactions, Orders, Invoices)'),
        ('MARKETING', 'Marketing (Promotions, Offers)'),
        ('AUTHENTICATION', 'Authentication (OTPs)'),
    ], string='Category', default='UTILITY', required=True)

    model_id = fields.Many2one(
        'ir.model',
        string='Applies to Model',
        required=True,
        ondelete='cascade',
        help='Odoo model for this template (e.g. sale.order, account.move, stock.picking, res.partner)'
    )
    model = fields.Char(related='model_id.model', store=True, readonly=True)

    header_type = fields.Selection([
        ('none', 'None'),
        ('text', 'Text Header'),
        ('document', 'Document (PDF Attachment)'),
        ('image', 'Image Attachment'),
    ], string='Header Type', default='document', required=True)

    header_text = fields.Char(string='Header Text (if text)', help='Dynamic or static header text')
    report_id = fields.Many2one(
        'ir.actions.report',
        string='PDF Report to Attach',
        domain="[('model', '=', model)]",
        help='Odoo PDF report that will be attached to the WhatsApp message'
    )

    body_text = fields.Text(
        string='Template Body',
        required=True,
        help="Template message body with placeholders like {{1}}, {{2}}, etc."
    )

    variable_ids = fields.One2many(
        'whatsapp.template.variable',
        'template_id',
        string='Dynamic Variables',
        copy=True
    )

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.constrains('template_name')
    def _check_template_name(self):
        for rec in self:
            if rec.template_name and not rec.template_name.islower() and ' ' in rec.template_name:
                raise ValidationError(_("Meta Template Name must be lowercase with underscores (no spaces)."))

    def _get_eval_context(self, record):
        """Prepare context for evaluating field expressions."""
        return {
            'object': record,
            'record': record,
            'env': self.env,
            'user': self.env.user,
            'format_date': lambda d: fields.Date.to_string(d) if d else '',
        }

    def render_body_parameters(self, record):
        """Returns ordered list of parameter values for the body components."""
        self.ensure_one()
        parameters = []
        for var in self.variable_ids.sorted(key=lambda r: r.sequence):
            val = var.get_value(record)
            parameters.append({'type': 'text', 'text': str(val or '')})
        return parameters

    def render_document_attachment(self, record):
        """Generate PDF attachment binary content and filename for the given record."""
        self.ensure_one()
        if self.header_type != 'document' or not self.report_id:
            return None, None

        report = self.report_id
        # Compatibility render across Odoo 16, 17, 18, 19
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report.report_name, record.ids)
        filename = f"{record.display_name or 'document'}.pdf".replace('/', '_').replace(' ', '_')
        return pdf_content, filename


class WhatsAppTemplateVariable(models.Model):
    _name = 'whatsapp.template.variable'
    _description = 'WhatsApp Template Dynamic Variable Mapping'
    _order = 'sequence asc'

    template_id = fields.Many2one('whatsapp.template', string='Template', ondelete='cascade')
    sequence = fields.Integer(string='Variable # (e.g. 1 for {{1}})', default=1, required=True)
    field_expression = fields.Char(
        string='Field Expression / Path',
        required=True,
        help="Field path (e.g. 'partner_id.name', 'name', 'amount_total', 'company_id.name')"
    )
    default_value = fields.Char(string='Fallback Value', default='')

    def get_value(self, record):
        """Safely extract field value by traversing path."""
        self.ensure_one()
        if not record or not self.field_expression:
            return self.default_value or ''

        try:
            expr_parts = self.field_expression.strip().split('.')
            val = record
            for part in expr_parts:
                val = getattr(val, part, None)
                if val is None:
                    break

            if val is not None:
                # If Many2one recordset
                if isinstance(val, models.BaseModel):
                    return val.display_name or self.default_value or ''
                # If float / currency
                if isinstance(val, float):
                    return f"{val:,.2f}"
                return str(val)
            return self.default_value or ''
        except Exception as e:
            _logger.warning("Error evaluating variable %s on %s: %s", self.field_expression, record, e)
            return self.default_value or ''
