import PyInstaller.__main__
import os
import platform
import sys

def get_platform_specific_args():
    """Get platform-specific PyInstaller arguments"""
    system = platform.system().lower()
    separator = ';' if os.name == 'nt' else ':'
    
    args = []
    
    # Platform-specific icon handling
    if system == 'windows':
        args.extend(['--icon=src/icon.ico'])
    elif system == 'darwin':  # macOS
        # Convert .ico to .icns if needed, or use a .icns file
        args.extend(['--icon=src/icon.ico'])  # PyInstaller can handle .ico on macOS
    # Linux doesn't need icon in build args
    
    # Add data files with correct separator
    args.extend([
        f'--add-data=src/styles.qss{separator}.',
        f'--add-data=src/icon.ico{separator}.',
    ])
    
    return args, separator

def build_application():
    """Build the application with cross-platform support"""
    system = platform.system().lower()
    app_name = 'Xtream-Companion'
    script_name = 'src/main.py'
    
    # Get platform-specific arguments
    platform_args, separator = get_platform_specific_args()
    
    # Base PyInstaller arguments
    pyinstaller_args = [
        f'--name={app_name}',
        '--onefile',
        '--windowed',  # No console window
        '--clean',     # Clean build
        '--noconfirm', # Overwrite without confirmation
    ]
    
    # Add platform-specific arguments
    pyinstaller_args.extend(platform_args)
    
    # Hidden imports for cross-platform compatibility
    hidden_imports = [
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
    ]
    
    for import_name in hidden_imports:
        pyinstaller_args.append(f'--hidden-import={import_name}')
    
    # Exclude unnecessary modules to reduce size
    excludes = [
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL.ImageTk',
        'PIL.ImageWin',
    ]
    
    for exclude in excludes:
        pyinstaller_args.append(f'--exclude-module={exclude}')
    
    # Add the main script
    pyinstaller_args.append(script_name)
    
    print(f"Building {app_name} for {system}...")
    print(f"PyInstaller arguments: {' '.join(pyinstaller_args)}")
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print(f"\nBuild completed successfully!")
        print(f"Executable location: dist/{app_name}{'.exe' if system == 'windows' else ''}")
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build_application()