#!/usr/bin/env python3
"""Test if the application can actually initialize."""

import sys
from PyQt6.QtWidgets import QApplication

print("=" * 70)
print("APPLICATION INITIALIZATION TEST")
print("=" * 70)

try:
    print("\n[1/3] Creating QApplication...")
    app = QApplication(sys.argv)
    print("✅ QApplication created")
    
    print("\n[2/3] Importing FacelessVideoApp class...")
    from faceless_video_app import FacelessVideoApp
    print("✅ FacelessVideoApp imported")
    
    print("\n[3/3] Initializing main window...")
    window = FacelessVideoApp()
    print("✅ Main window initialized")
    print("✅ All UI components loaded")
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS: APPLICATION INITIALIZES WITHOUT ERRORS")
    print("=" * 70)
    print("\nApplication is ready to use!")
    
except Exception as e:
    print(f"\n❌ ERROR DURING INITIALIZATION:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("❌ FAILURE: APPLICATION FAILED TO INITIALIZE")
    print("=" * 70)
    sys.exit(1)
