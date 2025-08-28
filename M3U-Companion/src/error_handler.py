"""
M3U Companion - Advanced Error Handler
Comprehensive error handling, logging, and user feedback system.
"""
import sys
import traceback
import logging
from datetime import datetime
from pathlib import Path
try:
    from .qt_compatibility import QMessageBox, QApplication, get_messagebox_critical, get_messagebox_warning, exec_dialog
except ImportError:
    from qt_compatibility import QMessageBox, QApplication, get_messagebox_critical, get_messagebox_warning, exec_dialog

class ErrorHandler:
    """M3U Companion - Advanced error handling and logging system."""
    
    def __init__(self, app_name="M3U Companion"):
        self.app_name = app_name
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging system."""
        # Create logs directory
        log_dir = Path.home() / ".m3u_companion" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler with rotation
        log_file = log_dir / f"m3u_companion_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logger.critical(f"Uncaught exception: {error_msg}")
        
        # Show user-friendly error dialog
        self.show_error_dialog(
            "Unexpected Error",
            f"An unexpected error occurred:\n\n{exc_value}\n\nPlease check the logs for details.",
            str(exc_value)
        )
    
    def show_error_dialog(self, title, message, details=None):
        """Show enhanced error dialog to user with better formatting."""
        try:
            try:
                from .qt_compatibility import QMessageBox, get_messagebox_critical
            except ImportError:
                from qt_compatibility import QMessageBox, get_messagebox_critical
            
            msg_box = QMessageBox()
            msg_box.setIcon(get_messagebox_critical())
            msg_box.setWindowTitle(f"M3U Companion - {title}")
            
            # Enhanced message formatting
            formatted_message = f"❌ {message}"
            if "Failed to" in message:
                formatted_message += "\n\n💡 Suggestions:\n• Check your internet connection\n• Verify the URL/file path is correct\n• Try a different media player"
            
            msg_box.setText(formatted_message)
            
            if details:
                msg_box.setDetailedText(f"Technical Details:\n{str(details)}")
            
            msg_box.exec()
            
        except Exception as e:
            # Enhanced fallback to console if GUI fails
            print(f"\n{'='*50}")
            print(f"ERROR DIALOG FAILED: {title}")
            print(f"Message: {message}")
            if details:
                print(f"Details: {details}")
            print(f"Dialog error: {e}")
            print(f"{'='*50}\n")
    
    def show_critical_error(self, title, message, details=None):
        """Show enhanced critical error dialog with recovery options."""
        try:
            try:
                from .qt_compatibility import QMessageBox, get_messagebox_critical
            except ImportError:
                from qt_compatibility import QMessageBox, get_messagebox_critical
            
            msg_box = QMessageBox()
            msg_box.setIcon(get_messagebox_critical())
            msg_box.setWindowTitle(f"M3U Companion - Critical Error")
            
            formatted_message = f"🚨 Critical Error: {title}\n\n{message}\n\n"
            formatted_message += "🔧 Recovery Options:\n"
            formatted_message += "• Restart the application\n"
            formatted_message += "• Check system requirements\n"
            formatted_message += "• Contact support if issue persists"
            
            msg_box.setText(formatted_message)
            
            if details:
                msg_box.setDetailedText(f"Technical Details:\n{str(details)}\n\nPlease include this information when reporting the issue.")
            
            msg_box.exec()
            
        except Exception as e:
            # Enhanced fallback to console if GUI fails
            print(f"\n{'='*60}")
            print(f"🚨 CRITICAL ERROR: {title}")
            print(f"Message: {message}")
            if details:
                print(f"Technical Details: {details}")
            print(f"Dialog System Error: {e}")
            print(f"{'='*60}\n")
    
    def show_warning(self, title, message, parent=None):
        """Show warning dialog to user."""
        try:
            msg = QMessageBox(parent)
            msg.setIcon(get_messagebox_warning())
            msg.setWindowTitle(f"{self.app_name} - {title}")
            msg.setText(message)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            exec_dialog(msg)
            
            self.logger.warning(f"{title}: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to show warning dialog: {e}")
    
    def log_info(self, message):
        """Log info message."""
        self.logger.info(message)
    
    def log_warning(self, message):
        """Log warning message."""
        self.logger.warning(message)
    
    def log_error(self, message, exception=None):
        """Log error message with optional exception."""
        if exception:
            self.logger.error(f"{message}: {exception}", exc_info=True)
        else:
            self.logger.error(message)
    
    def log_debug(self, message):
        """Log debug message."""
        self.logger.debug(message)

# Global error handler instance
error_handler = ErrorHandler()

def setup_global_exception_handler():
    """Setup global exception handler."""
    sys.excepthook = error_handler.handle_exception

# Decorator for error handling
def handle_errors(show_dialog=True, return_value=None):
    """Decorator to handle errors in functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(f"Error in {func.__name__}", e)
                
                if show_dialog:
                    error_handler.show_warning(
                        "Operation Failed",
                        f"Failed to {func.__name__.replace('_', ' ')}: {str(e)}"
                    )
                
                return return_value
        return wrapper
    return decorator

# Context manager for error handling
class ErrorContext:
    """Context manager for handling errors in code blocks."""
    
    def __init__(self, operation_name, show_dialog=True, reraise=False):
        self.operation_name = operation_name
        self.show_dialog = show_dialog
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            error_handler.log_error(f"Error in {self.operation_name}", exc_value)
            
            if self.show_dialog:
                error_handler.show_warning(
                    "Operation Failed",
                    f"Failed to {self.operation_name}: {str(exc_value)}"
                )
            
            if self.reraise:
                return False  # Re-raise the exception
            
            return True  # Suppress the exception
        
        return False
