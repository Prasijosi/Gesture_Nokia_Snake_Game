"""
Installation and Setup Script for Nokia Snake Game with Gesture Control
Automatically installs all required dependencies and verifies system configuration

Created by Prashiddha Joshi
"""

import subprocess
import sys
import os
import urllib.request

# Model download URL (used by gesture_controller.py)
HAND_LANDMARKER_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")
        return False

def check_package(package_name):
    """Check if a package is already installed"""
    try:
        __import__(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False

def get_package_name(package_spec):
    """Extract package name from package specification (e.g., 'opencv-python==4.8.1.78' -> 'opencv-python')"""
    for sep in ['==', '>=', '<=', '>', '<']:
        if sep in package_spec:
            return package_spec.split(sep)[0]
    return package_spec

def check_webcam():
    """Check if webcam is available"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True
        return False
    except Exception:
        return False

def download_model():
    """Download the MediaPipe hand landmarker model if not present"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, "models")
    model_path = os.path.join(models_dir, "hand_landmarker.task")
    
    # Check if model already exists and is valid
    if os.path.exists(model_path) and os.path.getsize(model_path) > 1000:
        print("✓ Hand landmarker model already downloaded")
        return True
    
    print("Downloading MediaPipe hand landmarker model...")
    try:
        os.makedirs(models_dir, exist_ok=True)
        urllib.request.urlretrieve(HAND_LANDMARKER_MODEL_URL, model_path)
        print("✓ Model downloaded successfully!")
        return True
    except Exception as e:
        print(f"✗ Failed to download model: {e}")
        print("  The model will be downloaded automatically when you first run the game.")
        return True  # Not critical - will be downloaded on first run

def main():
    """Main setup function"""
    print()
    print("🐍 Nokia Snake Game - Gesture Control Setup")
    print("   Created by Prashiddha Joshi")
    print("=" * 55)
    print()
    
    # List of required packages (matching requirements.txt)
    packages = [
        "mediapipe==0.10.13",
        "opencv-python==4.8.1.78", 
        "numpy==1.24.0",
        "pygame==2.5.1"
    ]
    
    print("📦 Step 1: Installing required packages...")
    print("-" * 55)
    
    all_success = True
    
    for package in packages:
        package_name = get_package_name(package)
        print(f"  Checking {package_name}...", end=" ")
        
        if not check_package(package_name):
            print("not found")
            print(f"    Installing {package}...")
            if not install_package(package):
                all_success = False
        else:
            print("✓ installed")
    
    print()
    print("📥 Step 2: Downloading ML models...")
    print("-" * 55)
    download_model()
    
    print()
    print("📷 Step 3: Checking webcam...")
    print("-" * 55)
    if check_webcam():
        print("  ✓ Webcam detected and working")
    else:
        print("  ⚠ Webcam not detected or not accessible")
        print("    Make sure your webcam is connected before running the game")
    
    print()
    print("=" * 55)
    
    if all_success:
        print("🎉 Setup completed successfully!")
        print()
        print("To start the game, run:")
        print("  python main.py")
        print()
        print("┌─────────────────────────────────────────────────────┐")
        print("│                  GAME CONTROLS                      │")
        print("├─────────────────────────────────────────────────────┤")
        print("│  👆 Move hand UP    → Snake moves up                │")
        print("│  👇 Move hand DOWN  → Snake moves down              │")
        print("│  👈 Move hand LEFT  → Snake moves left              │")
        print("│  👉 Move hand RIGHT → Snake moves right             │")
        print("│  🤏 Pinch gesture   → Speed boost                   │")
        print("│  ⬆️  UP gesture      → Restart game (when game over)│")
        print("│  ESC key           → Quit game                     │")
        print("└─────────────────────────────────────────────────────┘")
        print()
        print("📺 Two windows will open:")
        print("   • Game Window: Classic Nokia Snake gameplay")
        print("   • Gesture Window: Webcam feed with hand tracking")
    else:
        print("❌ Some packages failed to install.")
        print("Please install them manually using:")
        print("  pip install -r requirements.txt")
    
    print()

if __name__ == "__main__":
    main()