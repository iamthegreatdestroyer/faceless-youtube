import subprocess
import sys

# Try to run the app directly with python
result = subprocess.run(
    [sys.executable, "faceless_video_app.py"],
    cwd=r"C:\FacelessYouTube",
    capture_output=True,
    text=True,
    timeout=5
)

print("STDOUT:")
print(result.stdout[:500])
print("\nSTDERR:")
print(result.stderr[:500])
print(f"\nReturn code: {result.returncode}")
