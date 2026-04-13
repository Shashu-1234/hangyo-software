# 🍦 Hangyo Ice Cream — Distribution Manager v2.0

## ⚙️ SETUP (First Time Only)

Install Python 3.8+ from python.org, then run:
```
pip install reportlab pillow ttkbootstrap
```

## ▶️ HOW TO RUN
```
python run_app.py
```

## 🔐 DEFAULT LOGIN
- Username: admin
- Password: admin123

---

## ✅ ALL FEATURES

| Module | What it does |
|--------|-------------|
| 📊 Dashboard | Stats with date filter (Today/Week/Month/All), overdue payment alerts |
| 📦 Stock | Add/Edit/Delete products, Receive stock, Batch & Expiry tracking with FIFO alerts |
| 🧾 Orders & Billing | Create/Edit orders, PDF bill with SHOP COPY + DISTRIBUTOR COPY, payment due date, credit limit warning, WhatsApp reminder |
| 💰 Payments | Filter by status, record payments, WhatsApp reminder |
| 🚚 Deliveries | Mark as Delivered (stock deducts HERE not on order), Print daily route sheet PDF |
| 📋 Company Order | Create order list, Export PDF, Share on WhatsApp |
| 📖 Shop Khata | Full order + payment history per shop, outstanding balance |
| 📊 Monthly Report | Sales summary, top products, top shops, export PDF |
| ↩️ Returns | Record damaged/expired returns, stock auto-restored |
| 🏪 Manage Shops | Name, owner, phone, address, credit limit, notes |
| 👥 Manage Users | Add staff with limited access (no payments/reports) |
| 💾 Backup | One-click backup button in sidebar |

## 🔑 KEY FIXES IN v2.0
- ✅ Save button now works on Add/Edit Product, Add/Edit Shop
- ✅ Search bar is live — updates as you type, clears back to full list
- ✅ Mark Delivered actually works and deducts stock correctly
- ✅ Company Order PDF, WhatsApp, Delete all fixed
- ✅ No more <sqlite3.Row> text — all data displays correctly
- ✅ Stock deducted on DELIVERY not on order creation
- ✅ Bill PDF has Copy 1 (Shop) and Copy 2 (Distributor) on separate pages
- ✅ Payment due date field on every order
- ✅ Credit limit warning when creating orders
- ✅ All delete/payment/view-bill functions tested and working

## 📁 FILES
| File | Purpose |
|------|---------|
| run_app.py | Start the app |
| main.py | All UI screens |
| database.py | Database + queries |
| pdf_gen.py | PDF generation |
| ui_helpers.py | Reusable UI components |
| hangyo_data.db | Your data (auto-created) |
| backups/ | Auto-created backup folder |
