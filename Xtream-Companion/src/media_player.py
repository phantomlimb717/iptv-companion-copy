"""
Cross-platform media player manager for Xtream Companion.
Provides FFplay and MPV support with platform-specific executable names and command line arguments.
"""
import os
import sys
import platform
import subprocess
import shutil
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QRadioButton
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PlayerSelectionDialog(QDialog):
    """Dialog for selecting preferred media player"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Media Player")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        self.selected_player = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Choose your preferred media player:")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Player options
        self.button_group = QButtonGroup(self)
        
        # FFplay option
        ffplay_radio = QRadioButton("FFplay (FFmpeg)")
        ffplay_radio.setObjectName("ffplay")
        ffplay_radio.setChecked(True)  # Default selection
        self.button_group.addButton(ffplay_radio)
        layout.addWidget(ffplay_radio)
        
        ffplay_desc = QLabel("• Lightweight, built into FFmpeg\n• Good compatibility across platforms")
        ffplay_desc.setStyleSheet("color: #cccccc; margin-left: 20px; margin-bottom: 10px;")
        layout.addWidget(ffplay_desc)
        
        # MPV option
        mpv_radio = QRadioButton("MPV")
        mpv_radio.setObjectName("mpv")
        self.button_group.addButton(mpv_radio)
        layout.addWidget(mpv_radio)
        
        mpv_desc = QLabel("• Advanced media player\n• Better performance and features")
        mpv_desc.setStyleSheet("color: #cccccc; margin-left: 20px; margin-bottom: 15px;")
        layout.addWidget(mpv_desc)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def get_selected_player(self):
        """Get the selected player type"""
        checked_button = self.button_group.checkedButton()
        return checked_button.objectName() if checked_button else "ffplay"

class MediaPlayerManager:
    """Xtream Companion - Manages media player selection and execution across platforms."""
    
    def __init__(self):
        self.settings = QSettings("M3UChecker", "PlayerSettings")
        self.current_os = platform.system().lower()
        self.preferred_player = self.settings.value("preferred_player", "ffplay")
        
    def get_player_executable(self, player_type=None):
        """Xtream Companion - Get the appropriate executable name for the current platform."""
        if player_type is None:
            player_type = self.preferred_player
            
        if self.current_os == "windows":
            if player_type == "mpv":
                # Try both mpv.exe and mpvnet.exe on Windows
                for exe_name in ["mpvnet.exe", "mpv.exe"]:
                    if shutil.which(exe_name):
                        return exe_name
                return "mpvnet.exe"  # Default fallback
            else:
                return "ffplay.exe"
        else:
            # Linux, macOS, and other Unix-like systems
            if player_type == "mpv":
                return "mpv"
            else:
                return "ffplay"
    
    def check_player_availability(self, player_type=None):
        """Xtream Companion - Check if a media player is available on the system."""
        if player_type is None:
            player_type = self.preferred_player
            
        executable = self.get_player_executable(player_type)
        return shutil.which(executable) is not None
    
    def get_player_command(self, stream_url, player_type=None):
        """Generate the appropriate command line for playing a stream"""
        if player_type is None:
            player_type = self.preferred_player
            
        executable = self.get_player_executable(player_type)
        
        if player_type == "mpv":
            """Xtream Companion - Build command line arguments for the media player."""
            if self.current_os == "windows":
                # MPV on Windows with WASAPI audio output
                return [executable, "--fs", "--keep-open=no", "--ao=wasapi", stream_url]
            else:
                # MPV on Linux/macOS with PulseAudio/ALSA fallback
                return [executable, "--fs", "--keep-open=no", "--ao=pulse,alsa", stream_url]
        else:
            # FFplay command line arguments
            return [executable, "-fs", "-noborder", "-autoexit", stream_url]
    
    def play_stream(self, stream_url, parent_widget=None):
        """Xtream Companion - Play a stream URL using the selected media player."""
        # Check if preferred player is available
        if not self.check_player_availability():
            # Try alternative player
            alternative = "mpv" if self.preferred_player == "ffplay" else "ffplay"
            if self.check_player_availability(alternative):
                self.preferred_player = alternative
                self.settings.setValue("preferred_player", alternative)
            else:
                self._show_player_not_found_error(parent_widget)
                return False
        
        command = self.get_player_command(stream_url)
        
        try:
            subprocess.Popen(command)
            return True
        except FileNotFoundError:
            self._show_player_not_found_error(parent_widget)
            return False
        except Exception as e:
            self._show_playback_error(str(e), parent_widget)
            return False
    
    def set_preferred_player(self, player_type):
        """Set the preferred player and save to settings"""
        self.preferred_player = player_type
        self.settings.setValue("preferred_player", player_type)
    
    def show_player_selection_dialog(self, parent=None):
        """Xtream Companion - Show player selection dialog to user."""
        dialog = PlayerSelectionDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_player()
            self.set_preferred_player(selected)
            return True
        return False
    
    def _show_player_not_found_error(self, parent_widget):
        """Show error message when player is not found"""
        player_name = "MPV" if self.preferred_player == "mpv" else "FFplay"
        executable = self.get_player_executable()
        
        error_msg = f"{player_name} not found.\n\n"
        error_msg += f"Please ensure {executable} is installed and available in your system's PATH.\n\n"
        
        if self.current_os == "windows":
            if self.preferred_player == "mpv":
                error_msg += "For MPV on Windows:\n"
                error_msg += "• Download from https://mpv.io/installation/\n"
                error_msg += "• Or install MPV.NET from Microsoft Store\n"
            else:
                error_msg += "For FFplay on Windows:\n"
                error_msg += "• Download FFmpeg from https://ffmpeg.org/download.html\n"
                error_msg += "• Add the 'bin' directory to your system PATH\n"
        else:
            if self.preferred_player == "mpv":
                error_msg += "For MPV on Linux/macOS:\n"
                error_msg += "• Ubuntu/Debian: sudo apt install mpv\n"
                error_msg += "• macOS: brew install mpv\n"
            else:
                error_msg += "For FFplay on Linux/macOS:\n"
                error_msg += "• Ubuntu/Debian: sudo apt install ffmpeg\n"
                error_msg += "• macOS: brew install ffmpeg\n"
        
        QMessageBox.critical(parent_widget, "Media Player Error", error_msg)
    
    def _show_playback_error(self, error_message, parent_widget):
        """Show generic playback error"""
        QMessageBox.critical(
            parent_widget, 
            "Playback Error", 
            f"An error occurred while trying to play the stream:\n\n{error_message}"
        )
    
    def get_available_players(self):
        """Get list of available players on the system"""
        available = []
        for player in ["ffplay", "mpv"]:
            if self.check_player_availability(player):
                available.append(player)
        return available
    
    def get_player_info(self):
        """Get information about current player configuration"""
        return {
            "preferred_player": self.preferred_player,
            "executable": self.get_player_executable(),
            "available": self.check_player_availability(),
            "platform": self.current_os,
            "available_players": self.get_available_players()
        }
