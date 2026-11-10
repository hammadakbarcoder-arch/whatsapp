# -*- coding: utf-8 -*-
{
    'name': 'WhatsApp All-in-One Engine (No Meta API Needed · Free QR Scan & Meta Cloud API)',
    'version': '18.0.1.0.0',
    'category': 'Sales/Extra Tools',
    'summary': 'Run WhatsApp in Odoo with Free QR Scan or Meta API · Unlimited Numbers · Bulk Campaigns (Launch Offer: $20 for First 10 Buyers | Regular: $35)',
    'description': """
WhatsApp All-in-One Engine (Dual Mode: Free QR Path + Official Meta Cloud API)
==============================================================================
By Hammad Akbar

🔥 SPECIAL LAUNCH OFFER: $20 USD for the First 10 Buyers! (Standard Price: $35 USD after first 10 purchases)
🎁 EXCLUSIVE FIRST 10 BUYERS BONUS: 100% Free Setup Support & Custom Feature Guarantee!
📞 WhatsApp Direct Support: +92 310 9082711 | Email: rrajahammadakbar@gmail.com

Run WhatsApp from Odoo — NO Meta API needed, NO business approvals, NO per-message fees!
Connect UNLIMITED WhatsApp numbers with a simple QR scan, chat with customers, automate orders, invoices, and delivery slips, launch bulk marketing campaigns, and log calls inside Odoo Community or Enterprise.

Why Pay Monthly Subscriptions or Wait Weeks for Meta Approvals?
---------------------------------------------------------------
* **Launch Promo: $20 Once ($35 Regular) — Zero Per-Message Fees on QR:** Buy once, use forever. No recurring SaaS subscriptions.
* **Go Live in 60 Seconds with Free QR Path:** Scan with WhatsApp Mobile (Linked Devices) and start chatting instantly.
* **Dual Engine Architecture:** Free QR scan by default; connect official Meta Cloud API whenever you want!
* **Unlimited Numbers Across Unlimited Databases:** Add separate numbers for sales reps, support staff, and billing departments.
* **Instant Sales Order Automation:** SO confirmed -> customer gets WhatsApp notification with Quotation/Order PDF instantly.
* **Invoice & Delivery Automation:** Automatic Tax Invoice PDF on posting, and Delivery Slip PDF on warehouse dispatch.
* **Bulk Broadcast Campaigns:** Send personalized marketing messages and promotional flyers to 1000+ contacts with anti-spam throttle.
* **Customer-360 & Call Logs:** Keep an auditable record of voice/video calls and chat conversations on the partner timeline.
* **Cross-Version Support:** Built for Odoo 19.0, 18.0, 17.0 & 16.0 (Community & Enterprise).
    """,
    'author': 'Hammad Akbar',
    'maintainer': 'Hammad Akbar',
    'support': 'rrajahammadakbar@gmail.com',
    'website': 'https://apps.odoo.com/apps/modules/browse?author=Hammad%20Akbar',
    'license': 'OPL-1',
    'price': 20.00,
    'currency': 'USD',
    'depends': [
        'base',
        'sale_management',
        'account',
        'stock',
        'mail',
    ],
    'data': [
        'security/whatsapp_security.xml',
        'security/ir.model.access.csv',
        'data/whatsapp_default_data.xml',
        'views/whatsapp_account_views.xml',
        'views/whatsapp_campaign_views.xml',
        'views/whatsapp_call_log_views.xml',
        'views/res_config_settings_views.xml',
        'views/whatsapp_template_views.xml',
        'views/whatsapp_message_log_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/res_partner_views.xml',
        'views/whatsapp_menus.xml',
        'wizard/whatsapp_composer_views.xml',
    ],
    'images': [
        'static/description/banner_v18.png',
        'static/description/banner.png',
        'static/description/banner_v19.png',
        'static/description/banner_v17.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
