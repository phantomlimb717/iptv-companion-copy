import sys
from PyQt6.QtWidgets import QApplication
from ui import MainWindow

# --- The Definitive Windows Icon Fix ---
# This code tells the Windows operating system to treat this script as a
# unique application with its own identity, rather than just another
# instance of the Python interpreter. This forces Windows to use the icon
# set within the application on the taskbar.
# =========================================================================
if sys.platform == 'win32':
    import ctypes
    # A unique string to identify your application to the OS
    myappid = 'mycompany.xtreamcompanion.app.1.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
# =========================================================================

def main():
    """Main entry point for Xtream Companion."""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Xtream Companion")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("Xtream Companion")
        
        # PyQt6 handles high DPI automatically
        
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print("Error starting Xtream Companion:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()