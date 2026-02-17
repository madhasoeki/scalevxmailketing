# ScaleV x Mailketing Lead Management System

Aplikasi web berbasis Python untuk mengelola lead dari ScaleV dan mengintegrasikannya dengan Mailketing.

## 🎯 Fitur Utama

- **Lead Management**: Kelola lead dengan 3 status berbeda (Follow Up, Closing, Tidak Closing)
- **Webhook Integration**: Terima event real-time dari ScaleV (dengan signature verification)
- **Auto-Transfer**: Otomatis transfer lead ke Mailketing setelah 7 hari tidak closing
- **Dashboard**: Statistik dan monitoring lead secara real-time
- **Product Mapping**: Map produk ScaleV ke Mailketing lists dengan dropdown otomatis
- **API Testing**: Built-in API testing tools untuk Mailketing dan ScaleV
- **Ngrok Support**: Helper scripts untuk testing webhook di localhost

## 🔄 Cara Kerja

1. **Order Created** → Lead masuk ke status "Follow Up"
2. **Payment Received** → Lead pindah ke status "Closing"
3. **7 Hari Tidak Closing** → Lead pindah ke "Tidak Closing" dan dikirim ke Mailketing

## 📋 Requirements

- Python 3.8+
- ScaleV Account & API Key
- Mailketing Account & API Key

## 🚀 Instalasi

### 1. Clone atau Download Project

```bash
cd c:\laragon\www\scalevxmailketing
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi

```bash
python app.py
```

Aplikasi akan berjalan di: `http://localhost:5000`

## ⚙️ Konfigurasi

### 1. Setup API Keys

Buka halaman Settings di aplikasi dan masukkan:

- **ScaleV API Key**: Dapatkan dari dashboard ScaleV
- **ScaleV Webhook Secret**: Secret key untuk verifikasi webhook
- **Mailketing API Key**: Dapatkan dari dashboard Mailketing

### 2. Setup Webhook di ScaleV

**Untuk Development (Localhost):**

Gunakan Ngrok untuk expose localhost ke internet:

```bash
# Cara mudah (dengan helper):
python start_ngrok.py

# Atau manual:
ngrok http 5000
```

Web**Pilih produk dari dropdown** (otomatis muncul dari ScaleV API)
   - Atau input manual Product ID jika dropdown tidak muncul
4. **Pilih Mailketing List** dari dropdown (untuk lead tidak closing)
5. Klik "Simpan"

💡 **Tips:** Dropdown produk dan list akan muncul otomatis jika API keys sudah dikonfigurasi dengan benar di Settings.
1. Login ke dashboard ScaleV
2. Pergi ke Settings → Webhooks
3. Tambahkan webhook URL dari ngrok
4. Pilih events:
   - `order.created`
   - `order.paid`
5. Masukkan Webhook Secret yang sama dengan di aplikasi

📖 **Panduan lengkap testing webhook:** Lihat [WEBHOOK_TESTING.md](WEBHOOK_TESTING.md)

**Untuk Production:**

Deploy ke server cloud (Railway, Render, DigitalOcean, dll) dengan domain/IP public.

### 3. Tambah Product List

1. Pergi ke menu "Product Lists"
2. Klik "Tambah Product"
3. Masukkan:
   - Nama Produk
   - Product ID dari ScaleV
   - Pilih Mailketing List (untuk lead tidak closing)

## 📁 Struktur Folder

```
scalevxmailketing/
├── app.py                      # Main application
├── models.py                   # Database models
├── requirements.txt            # Dependencies
├── services/
│   ├── __init__.py
│   ├── scalev_service.py      # ScaleV API integration
│   ├── mailketing_service.py  # Mailketing API integration
│   └── lead_service.py        # Lead business logic
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Dashboard
│   ├── settings.html          # Settings page
│   ├── product_lists.html     # Product lists management
│   ├── leads.html             # Leads listing
│   └── lead_detail.html       # Lead detail page
└── scalevxmailketing.db       # SQLite database (auto-created)
```

## 🔧 Kustomisasi

### Ubah Durasi Follow Up

Di file `app.py`, function `check_expired_leads()`:

```python
expired_leads = lead_service.get_expired_follow_up_leads(days=7)  # Ubah angka 7
```

### Ubah Interval Check

Di file `app.py`, scheduler configuration:

```python
scheduler.add_job(
    func=check_expired_leads,
    trigger='interval',
    hours=1,  # Ubah interval check (dalam jam)
    ...
)
```

## 📊 Database Schema

### Settings
- API keys untuk ScaleV dan Mailketing
- Webhook secret

### ProductList
- Mapping produk ke Mailketing lists
- Product ID dari ScaleV

### Lead
- Informasi customer
- Status (follow_up, closing, not_closing)
- Order data
- Tracking dates

### LeadHistory
- Riwayat perubahan status lead

## 🔒 Keamanan

- Webhook signature verification
- Secret key untuk session
- API key disimpan di database

## ⚠️ Catatan Penting

1. **Webhook URL**: Pastikan aplikasi accessible dari internet agar ScaleV bisa mengirim webhook
2. **Background Scheduler**: Berjalan otomatis saat aplikasi running
3. **Database**: Menggunakan SQLite, untuk production disarankan gunakan PostgreSQL/MySQL

## 🐛 Troubleshooting

### Webhook tidak terima data
- Pastikan webhook URL accessible dari internet
- Cek webhook signature/secret sudah benar
- Lihat logs di terminal aplikasi

### Lead tidak pindah otomatis setelah 7 hari
- Pastikan aplikasi terus running
- Cek scheduler sudah aktif
- Lihat logs untuk error

### Tidak bisa koneksi ke Mailketing
- Test koneksi di halaman Settings
- Pastikan API key valid
- Cek network/firewall

## 📚 Dokumentasi API

- [ScaleV API Documentation](https://developers.scalev.id/docs/overview)
- [ScaleV Webhooks](https://developers.scalev.id/docs/enabling-webhooks-feature)
- [Mailketing API Documentation](https://mailketing.co.id/docs/api-get-all-list-from-account/)

## 📝 License

Free to use and modify.

## 💡 Support

Untuk pertanyaan atau bantuan, silakan buka issue di repository ini.

---

**Dibuat dengan ❤️ menggunakan Flask & Python**
