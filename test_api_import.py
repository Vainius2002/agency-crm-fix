#!/usr/bin/env python3
"""Test if API imports work correctly"""

try:
    from app import create_app
    from app.api import bp
    print("✓ Basic imports successful")
    
    app = create_app()
    print("✓ App creation successful")
    
    with app.app_context():
        from app.models import Brand, Company
        print("✓ Model imports successful")
        
        # Check if brands exist
        brands = Brand.query.join(Company).filter(Brand.status == 'active').all()
        print(f"✓ Found {len(brands)} brands in database")
        
        if brands:
            print("Sample brands:")
            for brand in brands[:3]:
                print(f"  - {brand.name} (Company: {brand.company.name})")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()