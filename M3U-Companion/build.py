"""
Build script for M3U Companion
Creates a standalone executable using PyInstaller
"""
import os
import sys
import subprocess
import shutil

def build_executable():
    """Build M3U Companion executable."""
    print("🔨 Building M3U Companion executable...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build command with Qt bindings exclusion
    build_cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "M3U-Companion",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        "--exclude-module", "PySide6",
        "--exclude-module", "PyQt5",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui", 
        "--hidden-import", "PyQt6.QtWidgets",
        "src/main.py"
    ]
    
    # Add icon if it exists (use absolute path)
    icon_path = os.path.abspath("src/icon.ico")
    if os.path.exists(icon_path):
        build_cmd.extend(["--icon", icon_path])
    else:
        print("⚠️ Icon file not found, building without icon")
    
    try:
        # Run PyInstaller
        subprocess.check_call(build_cmd)
        
        print("✅ Build completed successfully!")
        print(f"📦 Executable created: dist/M3U-Companion.exe")
        
        # Clean up build files
        if os.path.exists("build"):
            shutil.rmtree("build")
            print("🧹 Cleaned up build files")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
