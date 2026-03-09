"""
Migration script to add Telegram notification fields to Settings table
Run this once to update the database schema
"""

from app import app
from database import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Check if columns already exist
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(settings)"))
                columns = [row[1] for row in result]
                
                print("Current Settings columns:", columns)
                
                # Add telegram_bot_token column if not exists
                if 'telegram_bot_token' not in columns:
                    print("Adding telegram_bot_token column...")
                    conn.execute(text("ALTER TABLE settings ADD COLUMN telegram_bot_token VARCHAR(255)"))
                    conn.commit()
                    print("✓ Added telegram_bot_token column")
                else:
                    print("✓ telegram_bot_token column already exists")
                
                # Add telegram_chat_id column if not exists
                if 'telegram_chat_id' not in columns:
                    print("Adding telegram_chat_id column...")
                    conn.execute(text("ALTER TABLE settings ADD COLUMN telegram_chat_id VARCHAR(100)"))
                    conn.commit()
                    print("✓ Added telegram_chat_id column")
                else:
                    print("✓ telegram_chat_id column already exists")
                
                # Add telegram_enabled column if not exists
                if 'telegram_enabled' not in columns:
                    print("Adding telegram_enabled column...")
                    conn.execute(text("ALTER TABLE settings ADD COLUMN telegram_enabled BOOLEAN DEFAULT 0"))
                    conn.commit()
                    print("✓ Added telegram_enabled column")
                else:
                    print("✓ telegram_enabled column already exists")
                
                # Add telegram_debug_mode column if not exists
                if 'telegram_debug_mode' not in columns:
                    print("Adding telegram_debug_mode column...")
                    conn.execute(text("ALTER TABLE settings ADD COLUMN telegram_debug_mode BOOLEAN DEFAULT 0"))
                    conn.commit()
                    print("✓ Added telegram_debug_mode column")
                else:
                    print("✓ telegram_debug_mode column already exists")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("="*60)
    print("Running Telegram Settings Migration")
    print("="*60)
    migrate()
