# WhatsApp All-in-One Engine (Free QR Scan · No Meta API Needed · $20 Launch Offer · $35 Regular)

**ODOO 19 · NO META API NEEDED · FREE QR PATH · UNLIMITED NUMBERS · $20 LAUNCH OFFER ($35 REGULAR)**

Run WhatsApp from Odoo — no Meta API, no approval, no per-message fees.
Connect unlimited WhatsApp numbers with a simple QR scan, chat with customers, automate orders and invoices, send campaigns, log calls, and track every conversation inside Odoo Community or Enterprise. Use the free QR path by default — official Meta Cloud API is optional, not required.

🔥 **SPECIAL LAUNCH OFFER:** **$20 USD** for the First 10 Buyers! (Standard Price: **$35 USD** after first 10 purchases)

Developed by **Junaid & Hammad Akbar**

---

## ⚡ What Makes This #1 on Odoo App Store?

- **✓ Special Launch Pricing:** First 10 customers get it for just **$20 USD** ($35 regular).
- **✓ No Meta API Needed:** Connect via instant QR code scan in 60 seconds (like WhatsApp Web).
- **✓ No Approval Required:** Zero Meta business verification hurdles or template rejections.
- **✓ Zero Per-Message Fees on QR:** Buy once, use forever without recurring bills.
- **✓ Unlimited Numbers:** Connect multiple sales reps, support engineers, and warehouse phones across unlimited databases.
- **✓ Dual Engine Architecture:** Free QR scan by default; connect official Meta Cloud API whenever you want!
- **✓ Instant Sales Order Automation:** SO confirmed $\rightarrow$ customer gets WhatsApp notification with Quotation/Order PDF instantly.
- **✓ Invoices & Deliveries Automation:** Automatic Tax Invoice PDF on posting, and Delivery Slip PDF on warehouse dispatch.
- **✓ Replies in Discuss:** Customer WhatsApp replies route directly into Odoo Discuss & Chatter.
- **✓ Call Logs & Customer-360:** Track every voice/video call and meeting on the partner timeline.
- **✓ Bulk Marketing Campaigns:** Broadcast to 1,000+ targeted contacts with anti-spam throttle.
- **✓ Community & Enterprise:** Seamlessly runs across Odoo 19.0, 18.0, 17.0, and 16.0.

---

## 📦 Directory Structure

```
whatsapp_all_in_one_engine/
├── __init__.py
├── __manifest__.py
├── README.md
├── security/
│   ├── whatsapp_security.xml
│   └── ir.model.access.csv
├── data/
│   └── whatsapp_default_data.xml
├── models/
│   ├── __init__.py
│   ├── res_config_settings.py
│   ├── whatsapp_account.py        # Unlimited numbers & QR Session Engine
│   ├── whatsapp_campaign.py       # 1000+ contacts bulk broadcaster
│   ├── whatsapp_call_log.py       # Voice & Video call logging
│   ├── whatsapp_template.py
│   ├── whatsapp_message_log.py
│   ├── whatsapp_api_service.py
│   ├── res_partner.py
│   ├── sale_order.py
│   ├── account_move.py
│   └── stock_picking.py
├── views/
│   ├── whatsapp_account_views.xml
│   ├── whatsapp_campaign_views.xml
│   ├── whatsapp_call_log_views.xml
│   ├── res_config_settings_views.xml
│   ├── whatsapp_template_views.xml
│   ├── whatsapp_message_log_views.xml
│   ├── sale_order_views.xml
│   ├── account_move_views.xml
│   ├── stock_picking_views.xml
│   ├── res_partner_views.xml
│   └── whatsapp_menus.xml
├── wizard/
│   ├── __init__.py
│   ├── whatsapp_composer.py
│   └── whatsapp_composer_views.xml
├── tests/
│   ├── __init__.py
│   └── test_whatsapp.py
└── static/
    └── description/
        ├── icon.png
        ├── banner.png
        └── index.html
```

---

## 🚀 60-Second Setup

1. Copy `whatsapp_all_in_one_engine` to your Odoo `addons` directory.
2. Update App List in Odoo Developer Mode or run:
   ```bash
   odoo-bin -c config.conf -d <your_db> -i whatsapp_all_in_one_engine
   ```
3. Open **WhatsApp Engine $\rightarrow$ Accounts & QR Setup**:
   - Click **New**, enter your phone number and label.
   - Click **Generate QR Code**.
   - Open WhatsApp on your mobile $\rightarrow$ **Linked Devices** $\rightarrow$ **Link a Device** and scan.
4. You are live! Confirm any Sales Order or Invoice to watch automated PDFs dispatch instantly.

---

## 💼 Commercial Details

- **Price:** $20.00 USD (Launch offer for first 10 buyers | Regular: $35.00 USD)
- **License:** Odoo Proprietary License v1.0 (OPL-1)
- **Authors:** Junaid & Hammad Akbar
- **Repository / Support:** [Ninja Studio](https://apps.odoo.com/apps/modules/browse?author=Hammad%20Akbar)
