import sys
import os
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication
from faceless_video_app import FacelessVideoApp

print('✓ Creating QApplication...')
app = QApplication(sys.argv)

print('✓ Creating app instance...')
video_app = FacelessVideoApp()

print('✓ App initialization successful!')
print(f'✓ Assets dir: {video_app.assets_dir}')
print(f'✓ Output dir: {video_app.output_dir}')
print(f'✓ Log file: {video_app.video_log}')

# Check if directories exist
print(f'✓ Output dir exists: {os.path.exists(video_app.output_dir)}')
log_parent = os.path.dirname(video_app.video_log)
print(f'✓ Log file parent exists: {os.path.exists(log_parent)}')

sys.exit(0)
