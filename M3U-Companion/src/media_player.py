"""
Cross-platform media player manager for M3U Companion.
Provides FFplay and MPV support with platform-specific executable names and command line arguments.
"""
import os
import sys
import platform
import subprocess
import shutil
try:
    from .qt_compatibility import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QButtonGroup, QRadioButton, QMessageBox, QSettings,
                             exec_dialog, get_dialog_accepted, 
                             get_messagebox_critical, get_messagebox_warning, QT_LIBRARY)
except ImportError:
    from qt_compatibility import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QButtonGroup, QRadioButton, QMessageBox, QSettings,
                             exec_dialog, get_dialog_accepted, 
                             get_messagebox_critical, get_messagebox_warning, QT_LIBRARY)

class PlayerSelectionDialog(QDialog):
    """M3U Companion - Dialog for selecting preferred media player."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("M3U Companion - Select Media Player")
        self.setModal(True)
        self.resize(400, 200)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Choose your preferred media player:")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Player options
        self.button_group = QButtonGroup(self)
        
        # FFplay option
        ffplay_radio = QRadioButton("FFplay (Recommended)")
        ffplay_radio.setObjectName("ffplay")
        ffplay_radio.setChecked(True)  # Default selection
        self.button_group.addButton(ffplay_radio)
        layout.addWidget(ffplay_radio)
        
        ffplay_desc = QLabel("• Lightweight and fast\n• Part of FFmpeg suite\n• Excellent compatibility")
        ffplay_desc.setStyleSheet("margin-left: 20px; color: #666; font-size: 11px;")
        layout.addWidget(ffplay_desc)
        
        # MPV option
        mpv_radio = QRadioButton("MPV")
        mpv_radio.setObjectName("mpv")
        self.button_group.addButton(mpv_radio)
        layout.addWidget(mpv_radio)
        
        mpv_desc = QLabel("• Advanced media player\n• High-quality video rendering\n• Extensive customization")
        mpv_desc.setStyleSheet("margin-left: 20px; color: #666; font-size: 11px;")
        layout.addWidget(mpv_desc)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def get_selected_player(self):
        """Get the selected player type"""
        checked_button = self.button_group.checkedButton()
        return checked_button.objectName() if checked_button else "ffplay"

class MediaPlayerManager:
    """M3U Companion - Manages media player selection and execution across platforms."""
    
    def __init__(self):
        self.settings = QSettings("M3UCompanion", "PlayerSettings")
        self.current_os = platform.system().lower()
        self.preferred_player = self.settings.value("preferred_player", "ffplay")
        
    def get_player_executable(self, player_type=None):
        """M3U Companion - Get the appropriate executable name for the current platform."""
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
        """M3U Companion - Check if a media player is available on the system."""
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
            """M3U Companion - Build command line arguments for the media player."""
            if self.current_os == "windows":
                # MPV on Windows with WASAPI, DirectSound fallback
                return [executable, "--fs", "--keep-open=no", "--ao=wasapi,dsound", stream_url]
            elif self.current_os == "darwin":  # macOS
                # MPV on macOS with CoreAudio
                return [executable, "--fs", "--keep-open=no", "--ao=coreaudio", stream_url]
            else:
                # MPV on Linux with PulseAudio, ALSA, OSS fallback
                return [executable, "--fs", "--keep-open=no", "--ao=pulse,alsa,oss", stream_url]
        else:
            # FFplay command line arguments
            return [executable, "-fs", "-noborder", "-autoexit", stream_url]
    
    def play_stream(self, stream_url, parent_widget=None):
        """M3U Companion - Play a stream URL using the selected media player."""
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
        
        try:
            command = self.get_player_command(stream_url)
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        """M3U Companion - Show player selection dialog to user."""
        dialog = PlayerSelectionDialog(parent)
        if exec_dialog(dialog) == get_dialog_accepted():
            selected = dialog.get_selected_player()
            self.set_preferred_player(selected)
            return True
        return False
    
    def _show_player_not_found_error(self, parent_widget):
        """Show error message when player is not found"""
        player_name = "MPV" if self.preferred_player == "mpv" else "FFplay"
        msg = QMessageBox(parent_widget)
        msg.setIcon(get_messagebox_critical())
        msg.setWindowTitle("M3U Companion - Media Player Not Found")
        msg.setText(f"{player_name} media player not found!")
        msg.setInformativeText(
            f"Please install {player_name} or select a different player.\n\n"
            "FFplay: Install FFmpeg from https://ffmpeg.org/\n"
            "MPV: Install from https://mpv.io/"
        )
        exec_dialog(msg)
    
    def _show_playback_error(self, error_message, parent_widget):
        """Show error message for playback issues"""
        msg = QMessageBox(parent_widget)
        msg.setIcon(get_messagebox_warning())
        msg.setWindowTitle("M3U Companion - Playback Error")
        msg.setText("Failed to start media player!")
        msg.setInformativeText(f"Error: {error_message}")
        exec_dialog(msg)
