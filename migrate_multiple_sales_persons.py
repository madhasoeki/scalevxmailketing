"""
Migration script to convert single sales person fields to multiple sales persons (JSON arrays)
Run this ONCE after deploying the new code.
"""

import sqlite3
import json
import os
import sys

def migrate():
    """Migrate sales person fields from single to multiple (JSON arrays)"""
    
    # Check if database file exists
    db_path = 'scalevxmailketing.db'
    if not os.path.exists(db_path):
        print("=" * 60)
        print("❌ ERROR: Database file not found!")
        print("=" * 60)
        print("\nDatabase belum dibuat. Silakan jalankan aplikasi terlebih dahulu:")
        print("\n  python app.py")
        print("\nAplikasi akan otomatis membuat database dan tables.")
        print("Setelah itu, jalankan migration ini lagi.")
        print("\nAtau jika aplikasi sudah running di background/service,")
        print("pastikan database file ada di direktori yang sama dengan")
        print("migration script ini.")
        print("=" * 60)
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("MIGRATION: Single Sales Person -> Multiple Sales Persons")
    print("=" * 60)
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_list'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("\n❌ ERROR: Table 'product_list' belum ada!")
            print("\nDatabase ada tapi table belum dibuat.")
            print("Silakan jalankan aplikasi terlebih dahulu:")
            print("\n  python app.py")
            print("\nAplikasi akan otomatis membuat semua tables yang diperlukan.")
            print("Setelah itu, stop aplikasi dan jalankan migration ini lagi.")
            print("=" * 60)
            conn.close()
            sys.exit(1)
        
        # Check if old columns exist
        cursor.execute("PRAGMA table_info(product_list)")
        columns = [col[1] for col in cursor.fetchall()]
        
        has_old_columns = 'sales_person_id' in columns
        has_new_columns = 'sales_person_ids' in columns
        
        if not has_old_columns and has_new_columns:
            print("✓ Migration already completed. New columns exist.")
            print("=" * 60)
            return
        
        if not has_old_columns and not has_new_columns:
            print("\n✓ Fresh database detected. Adding new columns...")
            cursor.execute('''
                ALTER TABLE product_list 
                ADD COLUMN sales_person_ids TEXT
            ''')
            cursor.execute('''
                ALTER TABLE product_list 
                ADD COLUMN sales_person_names TEXT
            ''')
            cursor.execute('''
                ALTER TABLE product_list 
                ADD COLUMN sales_person_emails TEXT
            ''')
            conn.commit()
            print("✓ New columns added successfully!")
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            return
        
        # Migration needed - old columns exist
        print("\n1. Adding new columns...")
        
        # Add new columns
        if 'sales_person_ids' not in columns:
            cursor.execute('''
                ALTER TABLE product_list 
                ADD COLUMN sales_person_ids TEXT
            ''')
            print("   ✓ Added sales_person_ids")
        
        if 'sales_person_names' not in columns:
            cursor.execute('''
                ALTER TABLE product_list 
                ADD COLUMN sales_person_names TEXT
            ''')
            print("   ✓ Added sales_person_names")
        
        if 'sales_person_emails' not in columns:
            cursor.execute('''
                ALTER TABLE product_list 
                ADD COLUMN sales_person_emails TEXT
            ''')
            print("   ✓ Added sales_person_emails")
        
        conn.commit()
        
        # Migrate data from old columns to new columns
        print("\n2. Migrating data...")
        cursor.execute('''
            SELECT id, sales_person_id, sales_person_name, sales_person_email 
            FROM product_list
        ''')
        
        product_lists = cursor.fetchall()
        migrated = 0
        
        for pl_id, sp_id, sp_name, sp_email in product_lists:
            # If old data exists, convert to JSON array
            if sp_id:
                ids = json.dumps([sp_id])
                names = json.dumps([sp_name]) if sp_name else None
                emails = json.dumps([sp_email]) if sp_email else None
                
                cursor.execute('''
                    UPDATE product_list 
                    SET sales_person_ids = ?,
                        sales_person_names = ?,
                        sales_person_emails = ?
                    WHERE id = ?
                ''', (ids, names, emails, pl_id))
                
                migrated += 1
                print(f"   ✓ Migrated product_list ID {pl_id}: {sp_name}")
        
        conn.commit()
        print(f"\n✓ Migrated {migrated} product lists")
        
        # Note: We keep old columns for safety - they can be manually dropped later
        print("\n⚠️  Note: Old columns (sales_person_id, sales_person_name, sales_person_email)")
        print("   are kept for backup. You can drop them manually later if needed.")
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
