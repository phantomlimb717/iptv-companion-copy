import os
import sys
import requests
import base64
import subprocess
from datetime import datetime, timedelta, timezone
from functools import partial
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QInputDialog, QMessageBox, QDialog, QListWidget, QListWidgetItem, QSplitter, QStyle,
    QFileDialog, QStackedWidget, QButtonGroup, QRadioButton, QFrame, QTextEdit, QProgressBar, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QColor, QFont, QPixmap
from checker import check_account_status, get_live_categories, get_live_streams, get_full_epg_for_stream
from media_player import MediaPlayerManager

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- WORKER THREADS FOR XTREAM COMPANION ---
class CategoryWorker(QThread):
    result = pyqtSignal(object)
    def __init__(self, session, url, user, pwd):
        super().__init__()
        self.session, self.url, self.user, self.pwd = session, url, user, pwd
    def run(self): self.result.emit(get_live_categories(self.session, self.url, self.user, self.pwd))

class StreamWorker(QThread):
    result = pyqtSignal(object)
    def __init__(self, session, url, user, pwd, cat_id):
        super().__init__()
        self.session, self.url, self.user, self.pwd, self.cat_id = session, url, user, pwd, cat_id
    def run(self): self.result.emit(get_live_streams(self.session, self.url, self.user, self.pwd, self.cat_id))

class EPGGuideWorker(QThread):
    result = pyqtSignal(object)
    def __init__(self, session, url, user, pwd, stream_id):
        super().__init__()
        self.session, self.url, self.user, self.pwd, self.stream_id = session, url, user, pwd, stream_id
    def run(self): self.result.emit(get_full_epg_for_stream(self.session, self.url, self.user, self.pwd, self.stream_id))

class MultiAccountWorker(QThread):
    progress = pyqtSignal(int, dict)
    finished = pyqtSignal()
    status_update = pyqtSignal(str)
    
    def __init__(self, url, accounts, max_workers=8):
        super().__init__()
        self.url = url
        self.accounts = accounts
        self.max_workers = min(max_workers, len(accounts))
        self._stop_requested = False
        
    def stop(self):
        self._stop_requested = True
        
    def run(self):
        self.status_update.emit(f"Starting concurrent check of {len(self.accounts)} accounts with {self.max_workers} threads...")
        
        def check_single_account(index_account):
            index, account = index_account
            if self._stop_requested:
                return index, {"Status": "Cancelled", "Details": "Operation cancelled"}
            
            result = check_account_status(self.url, account['username'], account['password'])
            return index, result
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_index = {
                    executor.submit(check_single_account, (i, acc)): i 
                    for i, acc in enumerate(self.accounts)
                }
                
                completed_count = 0
                total_count = len(self.accounts)
                
                # Process completed tasks as they finish
                for future in as_completed(future_to_index):
                    if self._stop_requested:
                        break
                        
                    try:
                        index, result = future.result()
                        self.progress.emit(index, result)
                        completed_count += 1
                        
                        # Update status with progress
                        progress_pct = (completed_count / total_count) * 100
                        self.status_update.emit(f"Progress: {completed_count}/{total_count} ({progress_pct:.1f}%) - {result.get('Status', 'Unknown')} for account {index + 1}")
                        
                    except Exception as e:
                        error_result = {"Status": "Error", "Details": f"Check failed: {str(e)}"}
                        self.progress.emit(future_to_index[future], error_result)
                        completed_count += 1
                        
        except Exception as e:
            self.status_update.emit(f"Thread pool error: {str(e)}")
            
        self.status_update.emit(f"Completed checking {len(self.accounts)} accounts.")
        self.finished.emit()

# --- PLAYLIST DIALOG FOR XTREAM COMPANION ---
class PlaylistDialog(QDialog):
    def __init__(self, url, username, password, parent=None):
        super().__init__(parent)
        self.url, self.username, self.password = url, username, password
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'XtreamCompanion/1.0'})
        self.stream_worker = None
        self.epg_worker = None
        self.setWindowTitle(f"Xtream Companion - Playlist Viewer for {username}")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setGeometry(150, 150, 1200, 800)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.category_list = QListWidget()
        self.channel_table = QTableWidget()
        self.epg_guide_list = QListWidget()
        self.epg_guide_list.setObjectName("epgGuideList")
        self.channel_table.setColumnCount(2)
        self.channel_table.setHorizontalHeaderLabels(["Channel Name", "Actions"])
        header = self.channel_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.channel_table.setColumnWidth(1, 70)
        self.channel_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.channel_table.verticalHeader().setDefaultSectionSize(40)
        self.channel_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.channel_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        main_splitter.addWidget(self.category_list)
        main_splitter.addWidget(self.channel_table)
        main_splitter.addWidget(self.epg_guide_list)
        main_splitter.setSizes([250, 450, 500])
        self.layout.addWidget(main_splitter, 1)
        self.status_label = QLabel("Loading channel groups...")
        self.layout.addWidget(self.status_label, 0)
        self.category_list.currentItemChanged.connect(self.on_category_selected)
        self.channel_table.currentItemChanged.connect(self.on_channel_selected)
        self.channel_table.cellDoubleClicked.connect(self.play_stream_from_row)
        self.load_categories()
    def on_category_selected(self, current, previous):
        if not current: return
        if self.stream_worker and self.stream_worker.isRunning(): self.stream_worker.requestInterruption()
        self.epg_guide_list.clear()
        self.channel_table.setRowCount(0)
        category_id = current.data(Qt.ItemDataRole.UserRole)
        self.status_label.setText(f"Loading channels for '{current.text()}'...")
        self.stream_worker = StreamWorker(self.session, self.url, self.username, self.password, category_id)
        self.stream_worker.result.connect(self.populate_streams)
        self.stream_worker.start()
    def populate_streams(self, streams):
        self.channel_table.setRowCount(0)
        error_msg = streams.get('error') if isinstance(streams, dict) else None
        if not isinstance(streams, list) or error_msg:
            self.status_label.setText(f"Error loading streams: {error_msg or 'Unknown'}")
            return
        if not streams:
            self.status_label.setText("This channel group is empty.")
            return
        self.channel_table.setRowCount(len(streams))
        for row, stream in enumerate(streams):
            name_item = QTableWidgetItem(stream['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, stream['stream_id'])
            self.channel_table.setItem(row, 0, name_item)
            play_button = QPushButton()
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            play_button.setIcon(icon)
            play_button.setIconSize(QSize(20, 20))
            play_button.setFixedSize(36, 36)
            play_button.setObjectName("playStreamBtn")
            play_button.setToolTip(f"Play '{stream['name']}'")
            play_button.clicked.connect(partial(self.play_stream_from_row, row))
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(play_button)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            self.channel_table.setCellWidget(row, 1, cell_widget)
        self.status_label.setText(f"Loaded {len(streams)} channels. Select a channel to view its guide.")
    def on_channel_selected(self, current, previous):
        if not current or not current.tableWidget(): return
        row = current.row()
        item = self.channel_table.item(row, 0)
        if not item: return
        if self.epg_worker and self.epg_worker.isRunning(): self.epg_worker.requestInterruption()
        stream_id = item.data(Qt.ItemDataRole.UserRole)
        self.status_label.setText(f"Fetching guide for '{item.text()}'...")
        self.epg_guide_list.clear()
        self.epg_worker = EPGGuideWorker(self.session, self.url, self.username, self.password, stream_id)
        self.epg_worker.result.connect(self.populate_epg_guide)
        self.epg_worker.start()
    def populate_epg_guide(self, epg_data):
        self.epg_guide_list.clear()
        error_msg = epg_data.get('error') if isinstance(epg_data, dict) else None
        if error_msg or 'epg_listings' not in epg_data or not epg_data['epg_listings']:
            self.status_label.setText(f"EPG not available: {error_msg or 'No listings found.'}")
            return
        now = datetime.now(timezone.utc)
        start_window, end_window = now - timedelta(hours=12), now + timedelta(hours=12)
        now_playing_item = None
        for program in epg_data['epg_listings']:
            try:
                start_dt = datetime.fromtimestamp(int(program['start_timestamp']), tz=timezone.utc)
                end_dt = datetime.fromtimestamp(int(program['stop_timestamp']), tz=timezone.utc)
                if start_dt > end_window or end_dt < start_window: continue
                title = base64.b64decode(program['title']).decode('utf-8', 'ignore')
                desc = base64.b64decode(program['description']).decode('utf-8', 'ignore')
                start_local, end_local = start_dt.astimezone(), end_dt.astimezone()
                display_text = f"{start_local.strftime('%I:%M %p')} - {end_local.strftime('%I:%M %p')}\n{title}"
                item = QListWidgetItem(display_text)
                item.setToolTip(desc)
                font = QFont()
                if start_dt <= now < end_dt:
                    font.setBold(True)
                    item.setForeground(QColor("#4CAF50"))
                    now_playing_item = item
                elif start_dt < now:
                    item.setForeground(QColor("#9E9E9E"))
                item.setFont(font)
                self.epg_guide_list.addItem(item)
            except (KeyError, TypeError, ValueError): continue
        if now_playing_item: self.epg_guide_list.scrollToItem(now_playing_item, QListWidget.ScrollHint.PositionAtCenter)
        self.status_label.setText("EPG loaded successfully.")
    def play_stream_from_row(self, row, col=None):
        item = self.channel_table.item(row, 0)
        if not item: return
        stream_id = item.data(Qt.ItemDataRole.UserRole)
        stream_name = item.text()
        parsed_url = urlparse(self.url)
        stream_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{self.username}/{self.password}/{stream_id}"
        self.status_label.setText(f"Attempting to play: {stream_name}")
        self.launch_player(stream_url)
    def launch_player(self, stream_url):
        """Launch media player using the MediaPlayerManager"""
        if not hasattr(self, 'player_manager'):
            self.player_manager = MediaPlayerManager()
        
        success = self.player_manager.play_stream(stream_url, self)
        if success:
            self.status_label.setText(f"Playing stream with {self.player_manager.preferred_player.upper()}...")
        else:
            self.status_label.setText("Failed to launch media player.")
    def load_categories(self):
        worker = CategoryWorker(self.session, self.url, self.username, self.password)
        worker.result.connect(self.populate_categories)
        worker.start()
        self.category_worker = worker
    def populate_categories(self, categories):
        error_msg = categories.get('error') if isinstance(categories, dict) else None
        if not isinstance(categories, list) or error_msg:
            self.status_label.setText(f"Error loading categories: {error_msg or 'Unknown'}")
            return
        for cat in sorted(categories, key=lambda x: x.get('category_name', '')):
            item = QListWidgetItem(cat['category_name'])
            item.setData(Qt.ItemDataRole.UserRole, cat['category_id'])
            self.category_list.addItem(item)
        self.status_label.setText("Select a group to view channels.")



# --- XTREAM COMPANION MAIN APPLICATION WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.accounts = []
        self.player_manager = MediaPlayerManager()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Xtream Companion - IPTV Account Manager")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 10)
        
        mode_label = QLabel("Xtream Companion")
        mode_label.setStyleSheet("font-weight: bold; color: #0078d7; font-size: 12pt;")
        toolbar_layout.addWidget(mode_label)
        
        toolbar_layout.addStretch()
        
        # Enhanced player selection button
        player_button = QPushButton(f"🎬 Player: {self.player_manager.preferred_player.upper()}")
        player_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        player_button.clicked.connect(self.change_player)
        toolbar_layout.addWidget(player_button)
        
        main_layout.addLayout(toolbar_layout)
        
        # Setup Xtream UI directly
        # Title
        title_label = QLabel("Xtream Companion - IPTV Account Manager")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #0078d7; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # URL input section
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Server URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://example.com:8080")
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)
        
        # Account input section
        account_group = QGroupBox("Account Management")
        account_layout = QVBoxLayout(account_group)
        
        # Buttons for account management
        button_layout = QHBoxLayout()
        
        import_button = QPushButton("Import Accounts")
        import_button.clicked.connect(self.import_accounts)
        button_layout.addWidget(import_button)
        
        add_button = QPushButton("Add Account")
        add_button.clicked.connect(self.add_account_row)
        button_layout.addWidget(add_button)
        
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.clear_accounts)
        button_layout.addWidget(clear_button)
        
        account_layout.addLayout(button_layout)
        
        # Input table
        self.input_table = QTableWidget()
        self.input_table.setColumnCount(2)
        self.input_table.setHorizontalHeaderLabels(["Username", "Password"])
        self.input_table.horizontalHeader().setStretchLastSection(True)
        self.input_table.setMaximumHeight(200)
        account_layout.addWidget(self.input_table)
        
        main_layout.addWidget(account_group)
        
        # Check button with enhanced styling
        self.check_button = QPushButton("🚀 Check Accounts")
        self.check_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14pt;
                font-weight: bold;
                border-radius: 8px;
                margin: 8px 0px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.check_button.clicked.connect(self.run_checks)
        main_layout.addWidget(self.check_button)
        
        # Results section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels(["Username", "Status", "Connections", "Expiry", "Server URL", "Port", "Timezone", "Actions"])
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.results_table.setColumnWidth(7, 120)
        results_layout.addWidget(self.results_table)
        
        main_layout.addWidget(results_group)
        
        # Enhanced status label with styling
        self.status_label = QLabel("🔄 Ready to check accounts.")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11pt;
                color: #333;
                margin: 4px 0px;
            }
        """)
        main_layout.addWidget(self.status_label)
    
    def change_player(self):
        """Change the preferred media player"""
        if self.player_manager.show_player_selection_dialog(self):
            # Update button text
            sender = self.sender()
            sender.setText(f"Player: {self.player_manager.preferred_player.upper()}")
    
    def import_accounts(self):
        """Import accounts from a text file supporting multiple formats"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Accounts", "", "Text Files (*.txt);;All Files (*)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
            
            accounts = []
            lines = content.split('\n')
            server_url = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Format 1: First line is server URL, subsequent lines are username:password
                if i == 0 and line.startswith('http') and ('username=' not in line):
                    server_url = line.rstrip('/')
                    continue
                elif server_url and ':' in line and not line.startswith('http'):
                    # username:password format after server URL
                    parts = line.split(':', 1)  # Split only on first colon
                    if len(parts) == 2:
                        accounts.append((parts[0].strip(), parts[1].strip()))
                        continue
                
                # Format 2: Full M3U URLs with parameters
                if line.startswith('http') and 'username=' in line and 'password=' in line:
                    try:
                        from urllib.parse import urlparse, parse_qs
                        parsed = urlparse(line)
                        query_params = parse_qs(parsed.query)
                        
                        if 'username' in query_params and 'password' in query_params:
                            username = query_params['username'][0]
                            password = query_params['password'][0]
                            accounts.append((username, password))
                            
                            # Extract server URL from first M3U URL if not set
                            if not server_url:
                                server_url = f"{parsed.scheme}://{parsed.netloc}"
                        continue
                    except Exception:
                        pass
                
                # Legacy formats: Support |, :, , separators
                for separator in ['|', ':', ',']:
                    if separator in line:
                        parts = line.split(separator, 1)
                        if len(parts) == 2:
                            accounts.append((parts[0].strip(), parts[1].strip()))
                            break
            
            if accounts:
                # Set server URL if found
                if server_url:
                    self.url_input.setText(server_url)
                
                self.input_table.setRowCount(len(accounts))
                for row, (username, password) in enumerate(accounts):
                    self.input_table.setItem(row, 0, QTableWidgetItem(username))
                    self.input_table.setItem(row, 1, QTableWidgetItem(password))
                
                status_msg = f"Imported {len(accounts)} accounts"
                if server_url:
                    status_msg += f" with server URL: {server_url}"
                self.status_label.setText(status_msg)
            else:
                QMessageBox.warning(self, "Import Failed", "No valid accounts found in file.")
        
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import accounts: {str(e)}")
    
    def add_account_row(self):
        """Add a new row to the input table"""
        current_rows = self.input_table.rowCount()
        self.input_table.setRowCount(current_rows + 1)
        self.input_table.setItem(current_rows, 0, QTableWidgetItem(""))
        self.input_table.setItem(current_rows, 1, QTableWidgetItem(""))
    
    def clear_accounts(self):
        """Clear all accounts from the input table"""
        self.input_table.setRowCount(0)
        self.results_table.setRowCount(0)
        self.status_label.setText("All accounts cleared.")
    
    def run_checks(self):
        """Run Xtream account checks"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "URL Missing", "Please enter a valid server URL.")
            return
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            self.url_input.setText(url)
        
        self.accounts.clear()
        for row in range(self.input_table.rowCount()):
            username = self.input_table.item(row, 0).text().strip() if self.input_table.item(row, 0) else ""
            password = self.input_table.item(row, 1).text().strip() if self.input_table.item(row, 1) else ""
            if not username or not password:
                QMessageBox.warning(self, "Incomplete Data", f"Row {row + 1} is incomplete.")
                return
            self.accounts.append({'username': username, 'password': password})
        
        self._prepare_results_table(self.accounts)
        self.set_ui_enabled(False)
        self.status_label.setText(f"Checking {len(self.accounts)} accounts...")

        # Determine optimal thread count (max 16, min 2)
        max_workers = min(16, max(2, len(self.accounts) // 2))
        
        self.worker = MultiAccountWorker(url, self.accounts, max_workers)
        self.worker.progress.connect(self.update_result_row)
        self.worker.finished.connect(self.on_checking_finished)
        self.worker.status_update.connect(self.update_status)
        self.worker.start()
    
    def _prepare_results_table(self, accounts):
        """Prepare the results table"""
        self.results_table.setRowCount(len(accounts))
        for row, acc in enumerate(accounts):
            self.results_table.setItem(row, 0, QTableWidgetItem(acc['username']))
            self.results_table.setItem(row, 1, QTableWidgetItem("Pending..."))
            self.results_table.setItem(row, 2, QTableWidgetItem(""))
            self.results_table.setItem(row, 3, QTableWidgetItem(""))
            self.results_table.setItem(row, 4, QTableWidgetItem(""))
            self.results_table.setItem(row, 5, QTableWidgetItem(""))
            self.results_table.setItem(row, 6, QTableWidgetItem(""))
            # Column 7 (Actions) will be populated with buttons in update_result_row
    
    def update_result_row(self, row, result):
        """Update a row in the results table"""
        status = result.get("Status", "Error")
        status_item = QTableWidgetItem(status)
        if status == "Active": 
            status_item.setBackground(QColor("#2E7D32"))
        elif status in ["Expired", "Banned", "Disabled"]: 
            status_item.setBackground(QColor("#C62828"))
        else: 
            status_item.setBackground(QColor("#FF8F00"))
        
        self.results_table.setItem(row, 1, status_item)
        
        # Connections (Current/Max)
        active_cons = result.get("Active Connections", "N/A")
        max_cons = result.get("Max Connections", "N/A")
        connections_text = f"{active_cons}/{max_cons}" if active_cons != "N/A" and max_cons != "N/A" else "N/A"
        self.results_table.setItem(row, 2, QTableWidgetItem(connections_text))
        
        # Expiry Date
        self.results_table.setItem(row, 3, QTableWidgetItem(result.get("Expiry Date", "N/A")))
        
        # Server URL
        server_url = result.get("Server URL", "N/A")
        self.results_table.setItem(row, 4, QTableWidgetItem(server_url))
        
        # Port
        port = result.get("Port", "N/A")
        self.results_table.setItem(row, 5, QTableWidgetItem(str(port)))
        
        # Timezone
        timezone = result.get("Timezone", "N/A")
        self.results_table.setItem(row, 6, QTableWidgetItem(timezone))
        
        if status == "Active":
            playlist_button = QPushButton()
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            playlist_button.setIcon(icon)
            playlist_button.setIconSize(QSize(20, 20))
            playlist_button.setFixedSize(36, 36)
            playlist_button.setObjectName("viewPlaylistBtn")
            playlist_button.setToolTip("View Playlist & EPG")
            playlist_button.clicked.connect(partial(self.show_playlist, row))
            
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(playlist_button)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            self.results_table.setCellWidget(row, 7, cell_widget)
    
    def on_checking_finished(self):
        """Handle completion of account checking"""
        active_count = sum(1 for i in range(self.results_table.rowCount()) 
                          if self.results_table.item(i, 1) and 
                          self.results_table.item(i, 1).text() == "Active")
        
        self.status_label.setText(f"✅ Completed! Found {active_count} active accounts out of {len(self.accounts)} total.")
        self.set_ui_enabled(True)
        
        # Stop the worker thread
        if hasattr(self, 'worker') and self.worker:
            self.worker.stop()
    
    def update_status(self, message):
        """Update status label with progress information"""
        self.status_label.setText(message)
    
    def set_ui_enabled(self, enabled):
        """Enable/disable UI elements"""
        self.url_input.setEnabled(enabled)
        self.check_button.setEnabled(enabled)
        self.input_table.setEnabled(enabled)
    
    def show_playlist(self, row):
        """Show playlist for a specific account"""
        account = self.accounts[row]
        dialog = PlaylistDialog(self.url_input.text().strip(), account['username'], account['password'], self)
        dialog.exec()
    
    # Legacy methods for compatibility
    def _create_url_section(self):
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("domain.com or domain.com:port")
        self.import_button = QPushButton("Import from File")
        self.import_button.setObjectName("importBtn")
        self.import_button.clicked.connect(self.import_from_file)
        self.setup_button = QPushButton("Setup Accounts Manually")
        self.setup_button.clicked.connect(self.prompt_for_account_count)
        url_layout.addWidget(QLabel("Server URL:"))
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.import_button)
        url_layout.addWidget(self.setup_button)
        return url_layout

    def parse_account_file(self, lines):
        """Parse account file for Xtream credentials"""
        if not lines: 
            return None, None, "The selected file is empty."
        if "http" not in lines[0] and ":" in lines[0]:
            host = self.xtream_url_input.text().strip() if hasattr(self, 'xtream_url_input') else ""
            if not host: 
                return None, None, "Format Error: If file contains only user:pass, you must enter the Server URL first."
            accounts = []
            for i, line in enumerate(lines):
                if ":" not in line: 
                    return None, None, f"Format Error on line {i+1}: Expected 'username:password'."
                parts = line.split(":", 1)
                accounts.append({'username': parts[0].strip(), 'password': parts[1].strip()})
            return host, accounts, None
        elif lines[0].startswith("http"):
            # Check if all lines are HTTP URLs (template-02.txt format)
            all_urls = all(line.strip().startswith("http") for line in lines if line.strip())
            
            if all_urls:
                # Template-02.txt format: All lines are full M3U URLs
                accounts, base_host = [], None
                for i, line in enumerate(lines):
                    try:
                        parsed = urlparse(line.strip())
                        query_params = parse_qs(parsed.query)
                        
                        if 'username' not in query_params or 'password' not in query_params:
                            return None, None, f"Format Error on line {i+1}: URL missing username or password parameters."
                        
                        username = query_params['username'][0].strip()
                        password = query_params['password'][0].strip()
                        host = f"{parsed.scheme}://{parsed.netloc}"
                        
                        if base_host is None: 
                            base_host = host
                        elif base_host != host:
                            return None, None, f"Format Error on line {i+1}: All URLs must use the same server host."
                        
                        accounts.append({'username': username, 'password': password})
                    except Exception as e: 
                        return None, None, f"Format Error on line {i+1}: Could not parse the full M3U URL - {str(e)}"
                return base_host, accounts, None
            else:
                # Template-01.txt format: First line is URL, rest are username:password
                first_line_is_url = True
                try:
                    if len(lines) > 1 and lines[1].startswith("http"): 
                        first_line_is_url = False
                except IndexError: 
                    pass
                if first_line_is_url:
                    host, accounts = lines[0].strip(), []
                    for i, line in enumerate(lines[1:]):
                        if ":" not in line: 
                            return None, None, f"Format Error on line {i+2}: Expected 'username:password'."
                        parts = line.split(":", 1)
                        accounts.append({'username': parts[0].strip(), 'password': parts[1].strip()})
                    return host, accounts, None
        
        # Fallback: Try to parse as mixed format
        accounts, base_host = [], None
        for i, line in enumerate(lines):
            try:
                parsed = urlparse(line.strip())
                query_params = parse_qs(parsed.query)
                username, password = query_params['username'][0].strip(), query_params['password'][0].strip()
                host = f"{parsed.scheme}://{parsed.netloc}"
                if base_host is None: 
                    base_host = host
                accounts.append({'username': username, 'password': password})
            except Exception: 
                return None, None, f"Format Error on line {i+1}: Could not parse the full M3U URL."
        return base_host, accounts, None

    
    # Legacy UI creation methods - no longer used but kept for compatibility
    def _create_input_table_section(self):
        pass
    
    def _create_action_buttons(self):
        pass
    
    def _create_results_table(self):
        pass
    