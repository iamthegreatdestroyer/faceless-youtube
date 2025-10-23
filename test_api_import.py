#!/usr/bin/env python3
"""Quick test of API imports and functionality."""

import sys
sys.path.insert(0, '.')

try:
    from src.api.main import app
    print("✅ API imports successfully")
    print(f"✅ App has {len(app.routes)} routes")
    
    # List first 10 routes
    print("\nFirst 10 routes:")
    for route in app.routes[:10]:
        print(f"  - {route.path}")
    
    print("\n✅ API module is healthy")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
