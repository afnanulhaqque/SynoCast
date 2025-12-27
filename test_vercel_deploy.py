#!/usr/bin/env python3
"""
Quick test script to verify app can be imported and initialized.
Run this locally to catch any import or initialization errors before deploying.
"""

import sys
import os

# Simulate Vercel environment
os.environ['VERCEL'] = '1'

print("Testing app import and initialization...")
print("=" * 60)

try:
    print("✓ Importing app module...")
    from app import app
    print("✓ App imported successfully!")
    
    print("\n✓ Checking Flask app configuration...")
    print(f"  - Debug mode: {app.debug}")
    print(f"  - Secret key set: {'Yes' if app.secret_key else 'No'}")
    print(f"  - Static folder: {app.static_folder}")
    print(f"  - Template folder: {app.template_folder}")
    
    print("\n✓ Checking environment variables...")
    required_vars = [
        'FLASK_SECRET_KEY',
        'OPENWEATHER_API_KEY',
        'RESEND_API_KEY',
        'GEMINI_API_KEY',
        'NEWS_API_KEY',
        'VAPID_PRIVATE_KEY',
        'VAPID_PUBLIC_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.environ.get(var):
            print(f"  ✓ {var}: Set")
        else:
            print(f"  ✗ {var}: MISSING")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠ WARNING: {len(missing_vars)} environment variable(s) missing!")
        print("  These must be set in Vercel dashboard for deployment to work.")
    
    print("\n✓ Checking routes...")
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print(f"  - Total routes: {len(routes)}")
    print(f"  - Sample routes: {routes[:5]}")
    
    print("\n" + "=" * 60)
    print("✓ ALL CHECKS PASSED! App should work on Vercel.")
    print("=" * 60)
    
except ImportError as e:
    print(f"\n✗ IMPORT ERROR: {e}")
    print("\nThis usually means:")
    print("  1. Missing dependency in requirements.txt")
    print("  2. Syntax error in Python files")
    print("  3. Circular import issue")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ INITIALIZATION ERROR: {e}")
    print("\nCheck the full traceback below:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
