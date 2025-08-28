"""
M3U Companion - Main user interface
Modern PyQt6 interface for M3U playlist management and streaming.
"""
import sys
import os
try:
    from .qt_compatibility import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
        QListWidget, QListWidgetItem, QSplitter, QFrame, QProgressBar,
        QFileDialog, QMessageBox, QThread, QTimer,
        get_alignment_center, get_resize_mode_stretch, get_resize_mode_contents,
        get_resize_mode_fixed, get_selection_behavior_rows, get_edit_triggers_none, 
        get_frame_style_panel, get_user_role, get_orientation_horizontal, 
        get_orientation_vertical, get_pen_style_solid, pyqtSignal
    )
except ImportError:
    from qt_compatibility import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
        QListWidget, QListWidgetItem, QSplitter, QFrame, QProgressBar,
        QFileDialog, QMessageBox, QThread, QTimer,
        get_alignment_center, get_resize_mode_stretch, get_resize_mode_contents,
        get_resize_mode_fixed, get_selection_behavior_rows, get_edit_triggers_none, 
        get_frame_style_panel, get_user_role, get_orientation_horizontal, 
        get_orientation_vertical, get_pen_style_solid, pyqtSignal
    )
try:
    from .error_handler import error_handler, handle_errors, ErrorContext
    from .media_player import MediaPlayerManager
    from .m3u_parser import M3UParser, M3UChannel
except ImportError:
    from error_handler import error_handler, handle_errors, ErrorContext
    from media_player import MediaPlayerManager
    from m3u_parser import M3UParser, M3UChannel

class M3ULoaderWorker(QThread):
    """M3U Companion - Worker thread for loading M3U playlists."""
    
    progress_update = pyqtSignal(str)
    loading_finished = pyqtSignal(list, dict)  # channels, groups
    error_occurred = pyqtSignal(str)
    
    def __init__(self, source, is_url=True):
        super().__init__()
        self.source = source
        self.is_url = is_url
        self.parser = M3UParser()
        
        # Connect parser signals
        self.parser.progress_update.connect(self.progress_update.emit)
        self.parser.parsing_finished.connect(self.loading_finished.emit)
        self.parser.error_occurred.connect(self.error_occurred.emit)
    
    def run(self):
        """Load M3U playlist from URL or file."""
        if self.is_url:
            self.parser.parse_from_url(self.source)
        else:
            self.parser.parse_from_file(self.source)

class MainWindow(QMainWindow):
    """M3U Companion - Main application window."""
    
    def __init__(self):
        super().__init__()
        self.channels = []
        self.groups = {}
        self.current_channels = []
        self.media_player = MediaPlayerManager()
        self.loader_worker = None
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """M3U Companion - Initialize the user interface."""
        self.setWindowTitle("M3U Companion - M3U Playlist Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        self.create_header(main_layout)
        
        # Content area with splitter
        splitter = QSplitter(get_orientation_horizontal())
        main_layout.addWidget(splitter)
        
        # Left panel - Groups
        self.create_groups_panel(splitter)
        
        # Right panel - Channels
        self.create_channels_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self, layout):
        """Create the header with input controls."""
        header_frame = QFrame()
        header_frame.setFrameStyle(get_frame_style_panel())
        header_layout = QVBoxLayout(header_frame)
        
        # Title with modern dark styling
        title = QLabel("🎬 M3U Companion")
        title.setAlignment(get_alignment_center())
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #ffffff;
            margin: 16px;
            padding: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(74, 144, 226, 0.1), stop:1 rgba(53, 122, 189, 0.1));
            border-radius: 8px;
        """)
        header_layout.addWidget(title)
        
        # Input section
        input_layout = QHBoxLayout()
        
        # URL input
        url_label = QLabel("M3U URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/playlist.m3u")
        self.load_url_btn = QPushButton("🌐 Load from URL")
        self.load_url_btn.clicked.connect(lambda: self.load_from_url())
        self.load_url_btn.setToolTip("Load M3U playlist from internet URL")
        
        input_layout.addWidget(url_label)
        input_layout.addWidget(self.url_input, 1)
        input_layout.addWidget(self.load_url_btn)
        
        # File input
        self.load_file_btn = QPushButton("📁 Load from File")
        self.load_file_btn.clicked.connect(lambda: self.load_from_file())
        self.load_file_btn.setToolTip("Load M3U playlist from local file")
        input_layout.addWidget(self.load_file_btn)
        
        # Player selection
        self.player_btn = QPushButton("🎬 Player")
        self.player_btn.clicked.connect(lambda: self.select_player())
        self.player_btn.setToolTip("Configure media player (FFplay/MPV)")
        input_layout.addWidget(self.player_btn)
        
        header_layout.addLayout(input_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        header_layout.addWidget(self.progress_bar)
        
        # Status label with dark theme styling
        self.status_label = QLabel("🎬 Ready to load M3U playlist")
        self.status_label.setAlignment(get_alignment_center())
        self.status_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2a2a2a, stop:1 #1a1a1a);
                border: 2px solid #4a90e2;
                border-radius: 8px;
                padding: 12px 16px;
                color: #ffffff;
                font-weight: 600;
                font-size: 14px;
                margin: 4px;
            }
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addWidget(header_frame)
    
    def create_groups_panel(self, splitter):
        """Create the left panel for groups."""
        groups_widget = QWidget()
        groups_layout = QVBoxLayout(groups_widget)
        
        # Groups header with dark styling
        groups_header = QLabel("📂 Channel Groups")
        groups_header.setStyleSheet("""
            font-weight: 600;
            font-size: 16px;
            margin: 8px;
            padding: 8px 12px;
            color: #ffffff;
            background-color: #2a2a2a;
            border-radius: 6px;
            border-left: 4px solid #4a90e2;
        """)
        groups_layout.addWidget(groups_header)
        
        # Groups list
        self.groups_list = QListWidget()
        self.groups_list.itemClicked.connect(self.on_group_selected)
        groups_layout.addWidget(self.groups_list)
        
        # Group info with dark styling
        self.group_info = QLabel("Select a group to view channels")
        self.group_info.setStyleSheet("""
            color: #cccccc;
            font-size: 12px;
            margin: 8px;
            padding: 6px 8px;
            background-color: #2a2a2a;
            border-radius: 4px;
            font-style: italic;
        """)
        groups_layout.addWidget(self.group_info)
        
        splitter.addWidget(groups_widget)
    
    def create_channels_panel(self, splitter):
        """Create the right panel for channels."""
        channels_widget = QWidget()
        channels_layout = QVBoxLayout(channels_widget)
        
        # Channels header with modern styling
        channels_header_layout = QHBoxLayout()
        channels_header = QLabel("📺 Channels")
        channels_header.setStyleSheet("""
            font-weight: 600;
            font-size: 16px;
            margin: 8px;
            padding: 8px 12px;
            color: #ffffff;
            background-color: #2a2a2a;
            border-radius: 6px;
            border-left: 4px solid #4a90e2;
        """)
        channels_header_layout.addWidget(channels_header)
        
        # Enhanced search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search channels...")
        self.search_input.textChanged.connect(self.search_channels)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 200px;
                margin: 8px;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
                background-color: #333333;
            }
        """)
        channels_header_layout.addWidget(self.search_input)
        
        channels_layout.addLayout(channels_header_layout)
        
        # Channels table - Optimized layout
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(3)
        self.channels_table.setHorizontalHeaderLabels(["Channel", "Group", "Actions"])
        
        # Configure table - Cross-platform optimized column sizing
        header = self.channels_table.horizontalHeader()
        header.setSectionResizeMode(0, get_resize_mode_stretch())  # Channel - takes most space
        header.setSectionResizeMode(1, get_resize_mode_contents())  # Group - fits content
        header.setSectionResizeMode(2, get_resize_mode_fixed())  # Actions - fixed width for buttons
        header.resizeSection(2, 110)  # Optimized width for centered buttons
        
        # Cross-platform table styling
        self.channels_table.setShowGrid(True)
        self.channels_table.setGridStyle(get_pen_style_solid())
        self.channels_table.verticalHeader().setDefaultSectionSize(40)  # Consistent row height
        
        self.channels_table.setAlternatingRowColors(True)
        self.channels_table.setSelectionBehavior(get_selection_behavior_rows())
        self.channels_table.setEditTriggers(get_edit_triggers_none())
        
        channels_layout.addWidget(self.channels_table)
        
        # Channel info with dark styling
        self.channel_info = QLabel("Load an M3U playlist to view channels")
        self.channel_info.setStyleSheet("""
            color: #cccccc;
            font-size: 12px;
            margin: 8px;
            padding: 6px 8px;
            background-color: #2a2a2a;
            border-radius: 4px;
            font-style: italic;
        """)
        channels_layout.addWidget(self.channel_info)
        
        splitter.addWidget(channels_widget)
    
    def create_status_bar(self):
        """Create status bar."""
        self.statusBar().showMessage("M3U Companion ready")
    
    def apply_styles(self):
        """Apply unified dark theme styling to the interface."""
        self.setStyleSheet("""
            /* Main Window - Dark Theme */
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            /* Buttons - Modern Dark Style */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #357abd);
                color: #ffffff;
                border: 1px solid #2c5aa0;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                min-width: 90px;
                min-height: 16px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5ba0f2, stop:1 #4a90e2);
                border-color: #4a90e2;
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #357abd, stop:1 #2c5aa0);
                border-color: #1e3f73;
            }
            
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #666666;
                border-color: #2a2a2a;
            }
            
            /* Input Fields - Dark Theme */
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                selection-background-color: #4a90e2;
            }
            
            QLineEdit:focus {
                border-color: #4a90e2;
                background-color: #333333;
            }
            
            QLineEdit::placeholder {
                color: #888888;
            }
            
            /* Table Widget - Dark Theme */
            QTableWidget {
                background-color: #252525;
                alternate-background-color: #2a2a2a;
                gridline-color: #404040;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #ffffff;
                selection-background-color: #4a90e2;
            }
            
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #333333;
            }
            
            QTableWidget::item:selected {
                background-color: #4a90e2;
                color: #ffffff;
            }
            
            QTableWidget::item:hover {
                background-color: #333333;
            }
            
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #404040;
                font-weight: 600;
            }
            
            /* List Widget - Dark Theme */
            QListWidget {
                background-color: #252525;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #ffffff;
                outline: none;
            }
            
            QListWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #333333;
                border-radius: 3px;
                margin: 1px;
            }
            
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a90e2, stop:1 #357abd);
                color: #ffffff;
                border: none;
            }
            
            QListWidget::item:hover {
                background-color: #333333;
            }
            
            /* Frames - Dark Theme */
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 8px;
                margin: 4px;
            }
            
            /* Progress Bar - Dark Theme */
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 6px;
                text-align: center;
                height: 24px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-weight: 600;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a90e2, stop:0.5 #5ba0f2, stop:1 #4a90e2);
                border-radius: 5px;
                margin: 1px;
            }
            
            /* Labels - Dark Theme */
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            
            /* Splitter - Dark Theme */
            QSplitter::handle {
                background-color: #404040;
                width: 2px;
                height: 2px;
            }
            
            QSplitter::handle:hover {
                background-color: #4a90e2;
            }
            
            /* Scrollbars - Dark Theme */
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #4a90e2;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #5ba0f2;
            }
            
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #4a90e2;
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #5ba0f2;
            }
            
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
            }
            
            /* Enhanced Tooltips - Dark Theme */
            QToolTip {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #4a90e2;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            
            /* Status Bar - Dark Theme */
            QStatusBar {
                background-color: #1a1a1a;
                color: #ffffff;
                border-top: 1px solid #404040;
            }
        """)
    
    @handle_errors(show_dialog=True)
    def load_from_url(self):
        """Load M3U playlist from URL."""
        url = self.url_input.text().strip()
        if not url:
            error_handler.show_warning("Invalid Input", "Please enter a valid M3U URL", self)
            return
        
        # Validate URL format
        if not (url.startswith('http://') or url.startswith('https://')):
            error_handler.show_warning("Invalid URL", "URL must start with http:// or https://", self)
            return
        
        error_handler.log_info(f"Loading M3U playlist from URL: {url}")
        self.start_loading(url, is_url=True)
    
    @handle_errors(show_dialog=True)
    def load_from_file(self):
        """Load M3U playlist from file."""
        with ErrorContext("select M3U file"):
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "M3U Companion - Select M3U File", 
                "", 
                "M3U Files (*.m3u *.m3u8);;Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                error_handler.log_info(f"Loading M3U playlist from file: {file_path}")
                self.start_loading(file_path, is_url=False)
    
    def start_loading(self, source, is_url=True):
        """Start loading M3U playlist in background thread."""
        # Disable controls
        self.load_url_btn.setEnabled(False)
        self.load_file_btn.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Clear current data
        self.clear_data()
        
        # Start worker thread
        self.loader_worker = M3ULoaderWorker(source, is_url)
        self.loader_worker.progress_update.connect(self.update_status)
        self.loader_worker.loading_finished.connect(self.on_loading_finished)
        self.loader_worker.error_occurred.connect(self.on_loading_error)
        self.loader_worker.start()
    
    def update_status(self, message):
        """Update status label with enhanced styling."""
        self.status_label.setText(message)
        self.statusBar().showMessage(message)
        
        # Add visual feedback based on message type
        if "❌" in message or "Failed" in message:
            self.status_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #e74c3c, stop:1 #c0392b);
                    border: 2px solid #a93226;
                    border-radius: 8px;
                    padding: 12px 16px;
                    color: #ffffff;
                    font-weight: 600;
                    font-size: 14px;
                    margin: 4px;
                }
            """)
        elif "✅" in message or "▶️" in message or "🎬" in message:
            self.status_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #27ae60, stop:1 #229954);
                    border: 2px solid #1e8449;
                    border-radius: 8px;
                    padding: 12px 16px;
                    color: #ffffff;
                    font-weight: 600;
                    font-size: 14px;
                    margin: 4px;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2a2a2a, stop:1 #1a1a1a);
                    border: 2px solid #4a90e2;
                    border-radius: 8px;
                    padding: 12px 16px;
                    color: #ffffff;
                    font-weight: 600;
                    font-size: 14px;
                    margin: 4px;
                }
            """)
    
    def on_loading_finished(self, channels, groups):
        """Handle successful playlist loading."""
        self.channels = channels
        self.groups = groups
        self.current_channels = channels
        
        # Update UI
        self.populate_groups()
        self.populate_channels(channels)
        
        # Update status
        self.update_status(f"Loaded {len(channels)} channels in {len(groups)} groups")
        
        # Re-enable controls
        self.load_url_btn.setEnabled(True)
        self.load_file_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def on_loading_error(self, error_message):
        """Handle loading error."""
        error_handler.log_error(f"Failed to load playlist: {error_message}")
        error_handler.show_warning("Loading Error", f"Failed to load playlist:\n\n{error_message}", self)
        
        # Update status
        self.update_status("❌ Failed to load playlist")
        
        # Re-enable controls
        self.load_url_btn.setEnabled(True)
        self.load_file_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def populate_groups(self):
        """Populate the groups list."""
        self.groups_list.clear()
        
        # Add "All Channels" option
        all_item = QListWidgetItem("📺 All Channels")
        all_item.setData(get_user_role(), "ALL")
        self.groups_list.addItem(all_item)
        
        # Add groups
        for group_name in sorted(self.groups.keys()):
            item = QListWidgetItem(f"📂 {group_name}")
            item.setData(get_user_role(), group_name)
            self.groups_list.addItem(item)
        
        # Select "All Channels" by default
        self.groups_list.setCurrentRow(0)
        self.group_info.setText(f"Total: {len(self.channels)} channels")
    
    def populate_channels(self, channels):
        """Populate the channels table with optimized layout and enhanced styling."""
        self.channels_table.setRowCount(len(channels))
        
        for row, channel in enumerate(channels):
            # Channel name with enhanced styling and metadata
            channel_display = f"📺 {channel.name}"
            if channel.logo:
                channel_display += " 🖼️"
            name_item = QTableWidgetItem(channel_display)
            name_item.setToolTip(f"Channel: {channel.name}\nURL: {channel.url}\nLogo: {'Yes' if channel.logo else 'No'}")
            self.channels_table.setItem(row, 0, name_item)
            
            # Group with icon
            group_item = QTableWidgetItem(f"📂 {channel.group}")
            group_item.setToolTip(f"Group: {channel.group}")
            self.channels_table.setItem(row, 1, group_item)
            
            # Actions - Create container widget for proper alignment
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setAlignment(get_alignment_center())
            
            # Premium Play button with cross-platform styling
            play_btn = QPushButton("▶️ Play")
            play_btn.clicked.connect(lambda checked, ch=channel: self.play_channel(ch))
            play_btn.setToolTip(f"Play {channel.name}")
            play_btn.setFixedSize(90, 32)  # Fixed size for consistent alignment
            play_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #27ae60, stop:1 #229954);
                    color: #ffffff;
                    border: 2px solid #1e8449;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 12px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2ecc71, stop:1 #27ae60);
                    border-color: #27ae60;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #229954, stop:1 #1e8449);
                    border-color: #1a7339;
                }
                QPushButton:disabled {
                    background-color: #555555;
                    color: #888888;
                    border-color: #444444;
                }
            """)
            
            action_layout.addWidget(play_btn)
            self.channels_table.setCellWidget(row, 2, action_widget)
        
        self.channel_info.setText(f"Showing {len(channels)} channels")
    
    def on_group_selected(self, item):
        """Handle group selection."""
        group_name = item.data(get_user_role())
        
        if group_name == "ALL":
            self.current_channels = self.channels
            self.group_info.setText(f"Total: {len(self.channels)} channels")
        else:
            self.current_channels = self.groups.get(group_name, [])
            self.group_info.setText(f"{group_name}: {len(self.current_channels)} channels")
        
        self.populate_channels(self.current_channels)
        self.search_input.clear()
    
    def search_channels(self, query):
        """Search channels by name."""
        if not query.strip():
            self.populate_channels(self.current_channels)
            return
        
        query = query.lower()
        filtered_channels = [ch for ch in self.current_channels 
                           if query in ch.name.lower()]
        
        self.populate_channels(filtered_channels)
        self.channel_info.setText(f"Search results: {len(filtered_channels)} channels")
    
    @handle_errors(show_dialog=True)
    def play_channel(self, channel):
        """Play the selected channel with enhanced error handling and user feedback."""
        try:
            # Validate channel data
            if not channel or not hasattr(channel, 'url') or not channel.url:
                error_handler.log_error("Invalid channel data", ValueError("Channel URL is missing or invalid"))
                self.update_status("❌ Invalid channel data")
                return
            
            # Validate URL format
            if not any(channel.url.startswith(protocol) for protocol in ['http', 'https', 'rtmp', 'rtsp', 'udp', 'rtp']):
                error_handler.log_error(f"Unsupported URL format: {channel.url}", ValueError("Invalid stream URL format"))
                self.update_status(f"❌ Unsupported URL format: {channel.name}")
                return
            
            error_handler.log_info(f"Attempting to play channel: {channel.name} ({channel.url})")
            self.update_status(f"🔄 Starting playback: {channel.name}...")
            
            # Disable the play button temporarily to prevent double-clicks
            sender_btn = self.sender()
            if sender_btn and hasattr(sender_btn, 'setEnabled'):
                sender_btn.setEnabled(False)
                sender_btn.setText("🔄 Loading...")
            
            if self.media_player.play_stream(channel.url, channel.name):
                self.update_status(f"▶️ Playing: {channel.name}")
                error_handler.log_info(f"Successfully started playback: {channel.name}")
            else:
                self.update_status(f"❌ Failed to play: {channel.name}")
                error_handler.log_warning(f"Failed to start playback: {channel.name}")
            
            # Re-enable the button
            if sender_btn and hasattr(sender_btn, 'setEnabled'):
                sender_btn.setEnabled(True)
                sender_btn.setText("▶️ Play")
                
        except Exception as e:
            error_handler.log_error(f"Error playing channel {channel.name}", e)
            self.update_status(f"❌ Error playing: {channel.name} - {str(e)}")
            
            # Re-enable the button on error
            sender_btn = self.sender()
            if sender_btn and hasattr(sender_btn, 'setEnabled'):
                sender_btn.setEnabled(True)
                sender_btn.setText("▶️ Play")
    
    @handle_errors(show_dialog=True)
    def select_player(self):
        """Show player selection dialog."""
        with ErrorContext("configure media player"):
            if self.media_player.show_player_selection_dialog(self):
                player_name = "MPV" if self.media_player.preferred_player == "mpv" else "FFplay"
                self.update_status(f"🎬 Selected player: {player_name}")
                error_handler.log_info(f"Media player changed to: {player_name}")
    
    def clear_data(self):
        """Clear all loaded data."""
        self.channels = []
        self.groups = {}
        self.current_channels = []
        self.groups_list.clear()
        self.channels_table.setRowCount(0)
        self.group_info.setText("Select a group to view channels")
        self.channel_info.setText("Load an M3U playlist to view channels")
    
    def closeEvent(self, event):
        """Handle application close."""
        if self.loader_worker and self.loader_worker.isRunning():
            self.loader_worker.terminate()
            self.loader_worker.wait()
        event.accept()
