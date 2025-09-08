#!/usr/bin/env python
"""Add contact_type field to client_contacts table"""

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Adding contact_type field to client_contacts table...")
    
    with db.engine.connect() as conn:
        # Check existing columns in client_contacts
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('client_contacts')]
        
        # Add contact_type column if it doesn't exist
        if 'contact_type' not in columns:
            print("Adding contact_type column...")
            conn.execute(text("ALTER TABLE client_contacts ADD COLUMN contact_type VARCHAR(20) DEFAULT 'client'"))
            conn.commit()
            print("contact_type column added successfully!")
        else:
            print("contact_type column already exists")
    
    print("Database updated successfully!")
    print("- Added contact_type column with default value 'client'")