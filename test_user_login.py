#!/usr/bin/env python3
"""Test what password works for user login in agency-crm"""

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    email = "vainius.lunys123@gmail.com"
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        print(f"User found: {email}")
        print(f"Name: {user.first_name} {user.last_name}")
        print(f"Active: {user.is_active}")
        print(f"Role: {user.role}")
        
        # Test various passwords
        test_passwords = [
            "password123",  # The one we just set
            "password",
            "admin",
            "123456",
            "test",
            "vainius",
            "Password123",
            "admin123"
        ]
        
        print("\nTesting passwords:")
        for pwd in test_passwords:
            if user.check_password(pwd):
                print(f"✓ FOUND WORKING PASSWORD: '{pwd}'")
                break
            else:
                print(f"✗ Not: {pwd}")
    else:
        print(f"User {email} not found!")
        print("\nAvailable users:")
        for u in User.query.all():
            print(f"  - {u.email}")