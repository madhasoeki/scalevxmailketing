"""
Migration script to make product_list_id nullable in lead table
Run this once: python migrate_nullable_product_list.py
"""

def migrate():
    """Make product_list_id nullable in existing database"""
    from app import app, db
    
    with app.app_context():
        try:
            print("\n" + "="*60)
            print("MIGRATION: Make lead.product_list_id nullable")
            print("="*60 + "\n")
            
            # For SQLite, we need to recreate the table
            # But simpler way: just let it fail gracefully for new inserts
            # Or manually update database
            
            print("⚠️  SQLite tidak support ALTER COLUMN secara langsung.")
            print("\nOpsi 1 (Recommended): Reset database")
            print("  python reset.py")
            print("\nOpsi 2: Database baru akan otomatis pakai schema yang benar")
            print("  (Untuk instance/database baru)")
            print("\nOpsi 3: Manual - hapus file instance/scalevxmailketing.db")
            print("  lalu restart aplikasi untuk recreate dengan schema baru")
            
            print("\n✅ Jika Anda pakai database baru/kosong, skip migration ini.")
            print("   Schema sudah benar di models.py\n")
            
        except Exception as e:
            print(f"❌ Migration error: {str(e)}\n")

if __name__ == '__main__':
    migrate()
