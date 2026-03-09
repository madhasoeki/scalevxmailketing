import os
from app import app, db

with app.app_context():
    print("⚠️  WARNING: This will delete the entire database!")
    confirm = input("Type 'YES' to continue: ")
    
    if confirm != 'YES':
        print("❌ Cancelled")
        exit()
    
    print("\n🗑️  Dropping all tables...")
    db.drop_all()
    print("   ✓ All tables dropped")
    
    print("\n🔨 Creating new tables...")
    db.create_all()
    print("   ✓ All tables created")
    
    print("\n✅ Database recreated successfully!")
    print("   Fresh start - no data, clean schema")