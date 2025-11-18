#!/usr/bin/env python3
"""Check which dependencies are installed."""

required_modules = [
    'os', 'sys', 'logging', 'tempfile', 'json', 'datetime',
    'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
    'moviepy', 'gtts', 'requests', 'PIL',
    'google.oauth2.credentials', 'google_auth_oauthlib.flow',
    'googleapiclient.discovery', 'googleapiclient.http', 'urllib3', 'webbrowser'
]

print("=" * 60)
print("DEPENDENCY CHECK FOR FACELESS_VIDEO_APP.PY")
print("=" * 60)

missing = []
for module in required_modules:
    try:
        if '.' in module:
            parts = module.split('.')
            __import__(parts[0])
        else:
            __import__(module)
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module} - MISSING")
        missing.append(module)

print("\n" + "=" * 60)
if missing:
    print(f"MISSING DEPENDENCIES: {len(missing)}")
    for m in missing:
        print(f"  - {m}")
else:
    print("ALL DEPENDENCIES INSTALLED ✅")
print("=" * 60)
