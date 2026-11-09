# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestWhatsAppAllInOne(TransactionCase):

    def setUp(self):
        super(TestWhatsAppAllInOne, self).setUp()
        self.api_service = self.env['whatsapp.api.service']
        self.partner = self.env['res.partner'].create({
            'name': 'Test WhatsApp Customer',
            'phone': '0300 1234567',
        })

    def test_phone_sanitization(self):
        """Test international phone number sanitization."""
        # Test clean number with dashes and spaces
        phone = "+92 300-1234567"
        sanitized = self.api_service.sanitize_phone_number(phone, partner=self.partner)
        self.assertTrue(sanitized.startswith('92300'))
        self.assertEqual(len(sanitized), 12)

    def test_default_templates_exist(self):
        """Verify pre-installed default templates."""
        so_template = self.env.ref('whatsapp_all_in_one_engine.whatsapp_template_sales_order', raise_if_not_found=False)
        self.assertTrue(so_template, "Sales Order default template should exist")
        self.assertEqual(so_template.category, 'UTILITY')
        self.assertEqual(so_template.header_type, 'document')

        inv_template = self.env.ref('whatsapp_all_in_one_engine.whatsapp_template_customer_invoice', raise_if_not_found=False)
        self.assertTrue(inv_template, "Customer Invoice default template should exist")

    def test_message_log_creation(self):
        """Test creating and tracking WhatsApp audit logs."""
        log = self.env['whatsapp.message.log'].create({
            'name': 'Test Dispatched Notification',
            'partner_id': self.partner.id,
            'mobile_number': '923001234567',
            'state': 'sent',
            'meta_message_id': 'wamid.HBgLTest123',
        })
        self.assertEqual(log.state, 'sent')
        self.assertEqual(log.partner_id.whatsapp_message_count, 1)
