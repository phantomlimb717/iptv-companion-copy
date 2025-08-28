"""
M3U Companion - Qt Compatibility Layer
Provides cross-platform PyQt6/PySide6 compatibility with fallback support.
"""
import sys
import os

# Try to import Qt libraries in order of preference
QT_LIBRARY = None
QtWidgets = None
QtCore = None
QtGui = None

# First try PyQt6
try:
    from PyQt6 import QtWidgets, QtCore, QtGui
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
    QT_LIBRARY = "PyQt6"
    print(f"✅ Using {QT_LIBRARY}")
except ImportError as e:
    print(f"⚠️ PyQt6 not available: {e}")
    
    # Fallback to PySide6
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        from PySide6.QtWidgets import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *
        QT_LIBRARY = "PySide6"
        print(f"✅ Using {QT_LIBRARY}")
    except ImportError as e:
        print(f"⚠️ PySide6 not available: {e}")
        
        # Final fallback to PyQt5
        try:
            from PyQt5 import QtWidgets, QtCore, QtGui
            from PyQt5.QtWidgets import *
            from PyQt5.QtCore import *
            from PyQt5.QtGui import *
            QT_LIBRARY = "PyQt5"
            print(f"✅ Using {QT_LIBRARY} (fallback)")
        except ImportError as e:
            print(f"❌ No Qt library available: {e}")
            sys.exit(1)

# Signal compatibility
if QT_LIBRARY == "PyQt5":
    pyqtSignal = QtCore.pyqtSignal
elif QT_LIBRARY == "PyQt6":
    pyqtSignal = QtCore.pyqtSignal
else:  # PySide6
    pyqtSignal = QtCore.Signal

# Compatibility functions for different Qt versions
def get_qt_enum(enum_class, enum_name):
    """Get Qt enum value with compatibility across versions."""
    if QT_LIBRARY == "PyQt5":
        # PyQt5 uses different enum access
        return getattr(enum_class, enum_name)
    else:
        # PyQt6/PySide6 use nested enums
        return getattr(enum_class, enum_name)

def exec_dialog(dialog):
    """Execute dialog with version compatibility."""
    if QT_LIBRARY == "PyQt5":
        return dialog.exec_()
    else:
        return dialog.exec()

def get_alignment_center():
    """Get center alignment constant."""
    if QT_LIBRARY == "PyQt5":
        return Qt.AlignCenter
    else:
        return Qt.AlignmentFlag.AlignCenter

def get_orientation_horizontal():
    """Get horizontal orientation constant."""
    if QT_LIBRARY == "PyQt5":
        return Qt.Horizontal
    else:
        return Qt.Orientation.Horizontal

def get_orientation_vertical():
    """Get vertical orientation constant."""
    if QT_LIBRARY == "PyQt5":
        return Qt.Vertical
    else:
        return Qt.Orientation.Vertical

def get_pen_style_solid():
    """Get solid pen style constant."""
    if QT_LIBRARY == "PyQt5":
        return Qt.SolidLine
    else:
        return Qt.PenStyle.SolidLine

def get_resize_mode_stretch():
    """Get stretch resize mode."""
    if QT_LIBRARY == "PyQt5":
        return QHeaderView.Stretch
    else:
        return QHeaderView.ResizeMode.Stretch

def get_resize_mode_contents():
    """Get resize to contents mode."""
    if QT_LIBRARY == "PyQt5":
        return QHeaderView.ResizeToContents
    else:
        return QHeaderView.ResizeMode.ResizeToContents

def get_resize_mode_fixed():
    """Get fixed resize mode."""
    if QT_LIBRARY == "PyQt5":
        return QHeaderView.Fixed
    else:
        return QHeaderView.ResizeMode.Fixed

def get_selection_behavior_rows():
    """Get select rows behavior."""
    if QT_LIBRARY == "PyQt5":
        return QTableWidget.SelectRows
    else:
        return QTableWidget.SelectionBehavior.SelectRows

def get_edit_triggers_none():
    """Get no edit triggers."""
    if QT_LIBRARY == "PyQt5":
        return QTableWidget.NoEditTriggers
    else:
        return QTableWidget.EditTrigger.NoEditTriggers

def get_frame_style_panel():
    """Get styled panel frame style."""
    if QT_LIBRARY == "PyQt5":
        return QFrame.StyledPanel
    else:
        return QFrame.Shape.StyledPanel

def get_user_role():
    """Get user role constant."""
    if QT_LIBRARY == "PyQt5":
        return Qt.UserRole
    else:
        return Qt.ItemDataRole.UserRole

def get_dialog_accepted():
    """Get dialog accepted constant."""
    if QT_LIBRARY == "PyQt5":
        return QDialog.Accepted
    else:
        return QDialog.DialogCode.Accepted

def get_messagebox_critical():
    """Get critical message box icon."""
    if QT_LIBRARY == "PyQt5":
        return QMessageBox.Critical
    else:
        return QMessageBox.Icon.Critical

def get_messagebox_warning():
    """Get warning message box icon."""
    if QT_LIBRARY == "PyQt5":
        return QMessageBox.Warning
    else:
        return QMessageBox.Icon.Warning

# Export the current Qt library name for other modules
__all__ = [
    'QT_LIBRARY', 'QtWidgets', 'QtCore', 'QtGui', 'pyqtSignal',
    'exec_dialog', 'get_alignment_center', 'get_orientation_horizontal', 'get_orientation_vertical',
    'get_resize_mode_stretch', 'get_resize_mode_contents', 'get_resize_mode_fixed',
    'get_selection_behavior_rows', 'get_edit_triggers_none', 'get_pen_style_solid',
    'get_frame_style_panel', 'get_user_role', 'get_dialog_accepted',
    'get_messagebox_critical', 'get_messagebox_warning'
]
