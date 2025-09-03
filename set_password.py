#!/usr/bin/env python3
"""Set password for a user in agency-crm database"""

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Find user by email
    email = "vainius.lunys123@gmail.com"
    new_password = "password123"  # You can change this
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        user.set_password(new_password)
        db.session.commit()
        print(f"✓ Password updated for {email}")
        print(f"  New password: {new_password}")
        print("\nYou can now log into projects-crm with:")
        print(f"  Email: {email}")
        print(f"  Password: {new_password}")
    else:
        print(f"✗ User {email} not found in agency-crm database")
        
        # Show available users
        users = User.query.all()
        if users:
            print("\nAvailable users:")
            for u in users:
                print(f"  - {u.email} ({u.first_name} {u.last_name})")