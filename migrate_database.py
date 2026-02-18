"""
Database migration script to add new columns for the 3-list system
Run this ONCE to migrate your existing database to the new structure

Option 1: Run via Flask app
    flask shell
    >>> from migrate_database import migrate
    >>> migrate()

Option 2: Import in your app and call migrate()
    from migrate_database import migrate
    migrate()

Option 3: Use SQLite directly (manual migration)
"""

def migrate():
    """Run migration within Flask app context"""
    try:
        from database import db
        from app import app
        from sqlalchemy import text
        
        with app.app_context():
            print("\n" + "="*60)
            print("DATABASE MIGRATION - Adding new columns")
            print("="*60 + "\n")
            
            # Get database connection
            connection = db.engine.connect()
            
            # List of migrations to perform
            migrations = [
                # ProductList table migrations
                ("ALTER TABLE product_list ADD COLUMN store_id VARCHAR(100)", "Add store_id to product_list"),
                ("ALTER TABLE product_list ADD COLUMN store_name VARCHAR(255)", "Add store_name to product_list"),
                ("ALTER TABLE product_list ADD COLUMN sales_person_id VARCHAR(100)", "Add sales_person_id to product_list"),
                ("ALTER TABLE product_list ADD COLUMN sales_person_name VARCHAR(255)", "Add sales_person_name to product_list"),
                ("ALTER TABLE product_list ADD COLUMN sales_person_email VARCHAR(255)", "Add sales_person_email to product_list"),
                ("ALTER TABLE product_list ADD COLUMN mailketing_list_followup VARCHAR(100)", "Add mailketing_list_followup to product_list"),
                ("ALTER TABLE product_list ADD COLUMN mailketing_list_closing VARCHAR(100)", "Add mailketing_list_closing to product_list"),
                ("ALTER TABLE product_list ADD COLUMN mailketing_list_not_closing VARCHAR(100)", "Add mailketing_list_not_closing to product_list"),
                
                # Multiple Sales Persons support (JSON arrays)
                ("ALTER TABLE product_list ADD COLUMN sales_person_ids TEXT", "Add sales_person_ids (JSON) to product_list"),
                ("ALTER TABLE product_list ADD COLUMN sales_person_names TEXT", "Add sales_person_names (JSON) to product_list"),
                ("ALTER TABLE product_list ADD COLUMN sales_person_emails TEXT", "Add sales_person_emails (JSON) to product_list"),
                
                # Lead table migrations
                ("ALTER TABLE lead ADD COLUMN sales_person_name VARCHAR(255)", "Add sales_person_name to lead"),
                ("ALTER TABLE lead ADD COLUMN sales_person_email VARCHAR(255)", "Add sales_person_email to lead"),
                ("ALTER TABLE lead ADD COLUMN mailketing_list_id VARCHAR(100)", "Add mailketing_list_id to lead"),
            ]
            
            successful = 0
            skipped = 0
            failed = 0
            
            for sql, description in migrations:
                try:
                    print(f"Running: {description}...")
                    connection.execute(text(sql))
                    connection.commit()
                    print(f"  ✓ Success")
                    successful += 1
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'duplicate column' in error_msg or 'already exists' in error_msg:
                        print(f"  ⊘ Skipped (column already exists)")
                        skipped += 1
                    else:
                        print(f"  ✗ Error: {str(e)}")
                        failed += 1
            
            # Migrate existing data
            print("\nMigrating existing data...")
            
            # Copy mailketing_list_id to mailketing_list_closing for existing records
            try:
                result = connection.execute(text("""
                    UPDATE product_list 
                    SET mailketing_list_closing = mailketing_list_id 
                    WHERE mailketing_list_id IS NOT NULL 
                    AND mailketing_list_closing IS NULL
                """))
                connection.commit()
                rows_updated = result.rowcount
                if rows_updated > 0:
                    print(f"  ✓ Migrated {rows_updated} product lists: mailketing_list_id → mailketing_list_closing")
                else:
                    print(f"  ⊘ No data to migrate (mailketing_list_id)")
            except Exception as e:
                print(f"  ⚠ Warning during data migration: {str(e)}")
            
            # Migrate single sales person to multiple sales persons (JSON arrays)
            try:
                import json
                # Get all product lists with old sales person data but no new data
                result = connection.execute(text("""
                    SELECT id, sales_person_id, sales_person_name, sales_person_email
                    FROM product_list
                    WHERE sales_person_id IS NOT NULL 
                    AND (sales_person_ids IS NULL OR sales_person_ids = '')
                """))
                
                rows_to_migrate = result.fetchall()
                migrated_count = 0
                
                for row in rows_to_migrate:
                    pl_id = row[0]
                    sp_id = row[1]
                    sp_name = row[2]
                    sp_email = row[3]
                    
                    # Convert to JSON arrays
                    ids_json = json.dumps([sp_id])
                    names_json = json.dumps([sp_name]) if sp_name else None
                    emails_json = json.dumps([sp_email]) if sp_email else None
                    
                    # Update the record
                    connection.execute(text("""
                        UPDATE product_list
                        SET sales_person_ids = :ids,
                            sales_person_names = :names,
                            sales_person_emails = :emails
                        WHERE id = :id
                    """), {"ids": ids_json, "names": names_json, "emails": emails_json, "id": pl_id})
                    migrated_count += 1
                
                if migrated_count > 0:
                    connection.commit()
                    print(f"  ✓ Migrated {migrated_count} product lists: single sales person → multiple sales persons (JSON)")
                else:
                    print(f"  ⊘ No data to migrate (single → multiple sales persons)")
            except Exception as e:
                print(f"  ⚠ Warning during sales person migration: {str(e)}")
            
            connection.close()
            
            print("\n" + "="*60)
            print("MIGRATION SUMMARY")
            print("="*60)
            print(f"✓ Successful: {successful}")
            print(f"⊘ Skipped:    {skipped}")
            print(f"✗ Failed:     {failed}")
            print("="*60 + "\n")
            
            if failed == 0:
                print("✅ Migration completed successfully!")
                print("\n📋 NEXT STEPS:")
                print("1. Restart your Flask application")
                print("2. Check your Product Lists page")
                print("3. Update existing products to use the new 3-list structure:")
                print("   - Select Store")
                print("   - Select Product")
                print("   - Select Sales Person (optional)")
                print("   - Select 3 Mailketing Lists (Follow Up, Closing, Not Closing)")
                print("\n⚠️  IMPORTANT: Old products only have 'Closing' list configured.")
                print("   Please update them to add Follow Up and Not Closing lists!\n")
            else:
                print("⚠️  Migration completed with errors. Please check the log above.")
                
    except ImportError as e:
        print(f"\n❌ Import Error: {str(e)}")
        print("\nPlease run this migration from within the Flask app:")
        print("1. Start Flask shell: flask shell")
        print("2. Run: from migrate_database import migrate")
        print("3. Run: migrate()")
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("="*60)
    print("DATABASE MIGRATION SCRIPT")
    print("="*60)
    print("\nThis script will add new columns for the 3-tier system.")
    print("\nTo run this migration:")
    print("1. Make sure your Flask app is installed")
    print("2. Run: python -c \"from migrate_database import migrate; migrate()\"")
    print("\nOr start your Flask app and it will auto-migrate on first run.")
    print("="*60)

