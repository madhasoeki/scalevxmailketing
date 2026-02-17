# ScaleV x Mailketing Integration - 3-Tier Lead Management System

## 🎯 System Overview

Aplikasi ini mengintegrasikan ScaleV webhook dengan Mailketing untuk mengelola lead dalam 3 tahap:

1. **Follow Up** - Lead baru (kirim langsung saat order dibuat)
2. **Closing** - Lead yang sudah bayar
3. **Not Closing** - Lead yang tidak bayar setelah 7 hari

## 🆕 New Features (Latest Update)

### 1. Store-based Product Selection
- Pilih Store terlebih dahulu
- Product dimuat dinamis berdasarkan Store yang dipilih
- Mendukung multi-store management

### 2. Sales Person Filtering (Optional)
- **All Sales Mode**: Terima order dari semua CS (sales_person = NULL)
- **Specific Sales Mode**: Hanya terima order dari CS tertentu
- Matching otomatis berdasarkan email handler dari webhook

### 3. 3-Tier Mailketing List System
- **List Follow Up**: Lead dikirim langsung saat order dibuat
- **List Closing**: Lead dikirim saat payment status = 'paid'
- **List Not Closing**: Lead dikirim setelah 7 hari tidak bayar

## 📋 Setup Guide

### 1. Database Migration

**PENTING**: Jika Anda sudah memiliki database lama, jalankan migration script:

```powershell
python migrate_database.py
```

Script ini akan:
- Menambahkan kolom baru ke database
- Migrate data lama ke struktur baru
- Keamanan: Skip kolom yang sudah ada (idempoten)

### 2. Konfigurasi Product List

Masuk ke **Product Lists** page dan tambahkan product:

#### Step 1: Pilih Store
- Dropdown akan load semua stores dari ScaleV API
- Ketik untuk mencari store

#### Step 2: Pilih Product
- Dropdown akan load products dari store yang dipilih
- Mendukung search

#### Step 3: Pilih Sales Person (Opsional)
- **Leave blank** = All Sales (terima dari semua CS)
- **Select specific** = Hanya terima dari CS tertentu

#### Step 4: Pilih 3 Mailketing Lists
- **List Follow Up**: Untuk lead baru
- **List Closing**: Untuk lead yang bayar
- **List Not Closing**: Untuk lead yang tidak closing

## 🔄 Workflow

### Case 1: All Sales Mode (No Sales Person Filter)

```
1. Customer creates order for "Sedekah Jariyah"
2. Webhook received → Product matched
3. ✓ No sales person filter → Create lead
4. → Send to Follow Up list immediately
5. Customer pays → Send to Closing list
6. OR: After 7 days → Send to Not Closing list
```

### Case 2: Specific Sales Person Mode

```
1. Customer creates order for "Wakaf Masjid"
2. Webhook received → Product matched
3. Check handler email in webhook
4. IF handler matches → Create lead
   ELSE → Skip (log: sales person mismatch)
5. → Send to Follow Up list immediately
6. Customer pays → Send to Closing list
7. OR: After 7 days → Send to Not Closing list
```

## 🧪 Testing

### Test Follow Up List
1. Create test order via ScaleV
2. Check webhook log untuk konfirmasi:
   - Product matched
   - Sales person matched (if configured)
   - Lead created
   - **Sent to Follow Up list**

### Test Closing List
1. Create test order
2. Mark as paid in ScaleV
3. Check webhook log:
   - Payment status changed event
   - Lead moved to closing
   - **Sent to Closing list**

### Test Not Closing List

**Option 1: Manual Test (Instant)**
```
1. Go to Leads page
2. Find a Follow Up lead
3. Click "Test" button
4. ✓ Lead moved to Not Closing
5. ✓ Sent to Not Closing list
```

**Option 2: Scheduler (Automatic)**
```
Wait 7 days → Scheduler runs hourly → Auto move to Not Closing
```

## 🔧 API Endpoints

### New Endpoints

```
GET /api/scalev/stores
→ Get all stores

GET /api/scalev/stores/{store_id}/products
→ Get products from specific store

GET /api/scalev/stores/{store_id}/sales-people
→ Get sales people from specific store
```

## 💾 Database Schema

### ProductList
```
- store_id: VARCHAR(100) - Store ID dari ScaleV
- store_name: VARCHAR(255) - Nama store
- product_id: VARCHAR(100) - Product ID
- product_name: VARCHAR(255) - Nama product
- sales_person_id: VARCHAR(100) - NULL = All Sales
- sales_person_name: VARCHAR(255)
- sales_person_email: VARCHAR(255)
- mailketing_list_followup: VARCHAR(100)
- mailketing_list_closing: VARCHAR(100)
- mailketing_list_not_closing: VARCHAR(100)
```

### Lead
```
- sales_person_name: VARCHAR(255) - CS yang handle order ini
- sales_person_email: VARCHAR(255)
- mailketing_list_id: VARCHAR(100) - List terakhir yang dikirim
```

## 📝 Important Notes

### 1. Product Matching (Priority Order)
```
Priority 1: SKU match
Priority 2: Exact product name
Priority 3: Partial product name (for variants)
Priority 4: Variant unique ID
```

### 2. Sales Person Matching
- Matching by **email** (case-insensitive)
- Handler data from webhook: `data.handler.email`
- If NULL in database → Accept all

### 3. Mailketing Send Timing
- **Follow Up**: Immediately when lead created
- **Closing**: When payment_status = 'paid'
- **Not Closing**: After 7 days (scheduler) or manual test

## 🚨 Troubleshooting

### Lead not created from webhook?
```
Check log for:
1. Product matched? → If not, add product to Product Lists
2. Sales person matched? → Check email matches exactly
3. Handler data in webhook? → Check `data.handler.email` exists
```

### Not sent to Mailketing?
```
1. Check Mailketing API key configured in Settings
2. Check list IDs are correct (viewlist API)
3. Check webhook log for error messages
```

### Migration failed?
```
1. Backup database first!
2. Check Python version (3.8+)
3. Check database file permissions
4. Run migration again (it's safe - idempoten)
```

## 📊 Monitoring

### Logs to Monitor
```
1. Webhook logs: Check for product/sales person matching
2. Scheduler logs: Check for 7-day processing
3. Mailketing logs: Check for API errors
```

### Dashboard Stats
- Follow Up count
- Closing count
- Not Closing count
- Recent leads with status

## 🔐 Security

- HMAC signature verification on webhooks
- API keys stored in database (encrypted recommended)
- Sales person matching prevents unauthorized leads

## 📞 Support

For issues or questions:
1. Check logs in terminal
2. Review webhook payload in `payload example.txt`
3. Test with ngrok for local development

---

**Version**: 2.0 (3-Tier Sales Person System)
**Last Updated**: February 2026
