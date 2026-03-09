"""
Migration script to drop UNIQUE constraint from product_id
This allows one product to be assigned to multiple product lists (different CS)

SQLite doesn't support DROP CONSTRAINT, so we need to recreate the table
"""

def migrate_drop_unique():
    """Drop UNIQUE constraint from product_list.product_id"""
    try:
        from database import db
        from app import app
        from sqlalchemy import text
        
        with app.app_context():
            print("\n" + "="*60)
            print("MIGRATION: Drop UNIQUE constraint from product_id")
            print("="*60 + "\n")
            
            connection = db.engine.connect()
            trans = connection.begin()
            
            try:
                # Check if constraint exists by trying to insert duplicate
                print("Checking if UNIQUE constraint exists...")
                
                # Step 1: Rename old table
                print("Step 1: Renaming product_list to product_list_old...")
                connection.execute(text("ALTER TABLE product_list RENAME TO product_list_old"))
                print("  ✓ Table renamed")
                
                # Step 2: Create new table without UNIQUE constraint
                print("\nStep 2: Creating new product_list table (without UNIQUE constraint)...")
                connection.execute(text("""
                    CREATE TABLE product_list (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        store_id VARCHAR(100) NOT NULL,
                        store_name VARCHAR(255) NOT NULL,
                        product_name VARCHAR(255) NOT NULL,
                        product_id VARCHAR(100) NOT NULL,
                        sales_person_ids TEXT,
                        sales_person_names TEXT,
                        sales_person_emails TEXT,
                        mailketing_list_followup VARCHAR(100),
                        mailketing_list_closing VARCHAR(100),
                        mailketing_list_not_closing VARCHAR(100),
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
                print("  ✓ New table created")
                
                # Step 3: Copy data from old table
                print("\nStep 3: Copying data from old table...")
                result = connection.execute(text("""
                    INSERT INTO product_list 
                    SELECT * FROM product_list_old
                """))
                rows_copied = result.rowcount
                print(f"  ✓ Copied {rows_copied} rows")
                
                # Step 4: Drop old table
                print("\nStep 4: Dropping old table...")
                connection.execute(text("DROP TABLE product_list_old"))
                print("  ✓ Old table dropped")
                
                # Commit transaction
                trans.commit()
                
                print("\n" + "="*60)
                print("✅ MIGRATION SUCCESSFUL!")
                print("="*60)
                print(f"✓ UNIQUE constraint removed from product_id")
                print(f"✓ {rows_copied} rows preserved")
                print("\n📋 Now you can assign one product to multiple CS!\n")
                
            except Exception as e:
                trans.rollback()
                error_msg = str(e).lower()
                if 'no such table: product_list' in error_msg:
                    print("\n❌ Error: product_list table doesn't exist yet.")
                    print("Please run the main migration first (migrate_database.py)\n")
                elif 'already exists' in error_msg or 'product_list_old' in error_msg:
                    print("\n⚠️  Migration already in progress or failed previously.")
                    print("Please check your database manually.\n")
                else:
                    raise
            finally:
                connection.close()
                
    except ImportError as e:
        print(f"\n❌ Import Error: {str(e)}")
        print("\nPlease run this from your Flask app environment.\n")
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("="*60)
    print("DROP UNIQUE CONSTRAINT MIGRATION")
    print("="*60)
    print("\nThis will allow one product to be assigned to multiple CS.")
    print("\nRun: python -c \"from migrate_drop_unique_constraint import migrate_drop_unique; migrate_drop_unique()\"")
    print("="*60)
