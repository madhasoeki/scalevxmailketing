"""
IMPORTANT: Timezone Migration Notice
=====================================

Aplikasi sekarang menyimpan semua datetime dalam WIB (UTC+7) bukan UTC.

UNTUK DATABASE BARU (Belum ada data):
--------------------------------------
Tidak perlu apa-apa, langsung git pull dan restart.


UNTUK DATABASE YANG SUDAH ADA DATA:
------------------------------------
Data lama mungkin akan tampil 7 jam lebih awal.

OPSI 1: Biarkan saja (Recommended untuk data sedikit)
- Data lama akan tampil 7 jam lebih awal
- Data baru sudah benar
- Tidak kehilangan data

OPSI 2: Reset database (Untuk data testing)
```bash
cd ~/scalevxmailketing
python3 reset.py
```

OPSI 3: Manual migration (Advanced - untuk data production)
```python
# Login ke VPS, masuk ke Python shell
cd ~/scalevxmailketing
source venv/bin/activate
python3

# Di Python shell:
from app import app, db
from models import Lead, Settings, ProductList, LeadHistory
from datetime import timedelta

with app.app_context():
    # Add 7 hours to all existing datetime fields
    for lead in Lead.query.all():
        if lead.created_at:
            lead.created_at = lead.created_at + timedelta(hours=7)
        if lead.updated_at:
            lead.updated_at = lead.updated_at + timedelta(hours=7)
        if lead.follow_up_start:
            lead.follow_up_start = lead.follow_up_start + timedelta(hours=7)
        if lead.closed_at:
            lead.closed_at = lead.closed_at + timedelta(hours=7)
        if lead.sent_to_mailketing_at:
            lead.sent_to_mailketing_at = lead.sent_to_mailketing_at + timedelta(hours=7)
    
    for pl in ProductList.query.all():
        if pl.created_at:
            pl.created_at = pl.created_at + timedelta(hours=7)
        if pl.updated_at:
            pl.updated_at = pl.updated_at + timedelta(hours=7)
    
    for s in Settings.query.all():
        if s.created_at:
            s.created_at = s.created_at + timedelta(hours=7)
        if s.updated_at:
            s.updated_at = s.updated_at + timedelta(hours=7)
    
    for h in LeadHistory.query.all():
        if h.created_at:
            h.created_at = h.created_at + timedelta(hours=7)
    
    db.session.commit()
    print("Migration complete!")
```

Update & Restart:
```bash
cd ~/scalevxmailketing
git pull
sudo systemctl restart scalevxmailketing
```
