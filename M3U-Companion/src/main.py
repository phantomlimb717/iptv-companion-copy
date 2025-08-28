"""
M3U Companion - Main entry point
A comprehensive M3U playlist viewer and stream player.
"""
import sys
import os
from qt_compatibility import QApplication, QT_LIBRARY, Qt
from error_handler import setup_global_exception_handler, error_handler
from ui import MainWindow

# Windows taskbar icon fix
# =========================================================================
# This is a workaround for Windows to display the correct icon in the taskbar.
# By default, Windows groups Python applications under the Python icon instead
# of using the application's own icon. This is because Windows identifies 

def main():
    """Main entry point for M3U Companion."""
    # Setup global exception handling
    setup_global_exception_handler()
    
    try:
        error_handler.log_info(f"Starting M3U Companion with {QT_LIBRARY}")
        
        app = QApplication(sys.argv)
        app.setApplicationName("M3U Companion")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("M3U Companion")
        
        # Cross-platform High DPI support
        if hasattr(app, 'setAttribute'):
            try:
                # PyQt6/PySide6 style
                app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
                app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
                
                # Additional cross-platform DPI settings
                if sys.platform == "win32":
                    app.setAttribute(Qt.ApplicationAttribute.AA_DisableWindowContextHelpButton, True)
                elif sys.platform == "darwin":
                    app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
                    
            except AttributeError:
                try:
                    # PyQt5 style fallback
                    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
                    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
                except AttributeError:
                    pass
        
        # Cross-platform style and theme
        if sys.platform == "darwin":
            app.setStyle('macintosh')
        elif sys.platform.startswith("linux"):
            app.setStyle('fusion')  # Modern look on Linux
        # Windows uses native style by default
        
        error_handler.log_info("Creating main window")
        window = MainWindow()
        window.show()
        
        error_handler.log_info("Application started successfully")
        exit_code = app.exec() if hasattr(app, 'exec') else app.exec_()
        
        error_handler.log_info("Application closed normally")
        sys.exit(exit_code)
        
    except Exception as e:
        error_handler.log_error("Failed to start M3U Companion", e)
        error_handler.show_critical_error(
            "Startup Error",
            f"Failed to start M3U Companion: {str(e)}",
            str(e)
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
