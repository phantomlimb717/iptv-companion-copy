"""
M3U Companion - M3U playlist parser and manager.
Handles M3U file parsing, URL loading, and channel organization.
"""
import re
import requests
try:
    from .error_handler import error_handler
except ImportError:
    from error_handler import error_handler
from urllib.parse import urlparse, urljoin
try:
    from .qt_compatibility import QObject, pyqtSignal, QT_LIBRARY
except ImportError:
    from qt_compatibility import QObject, pyqtSignal, QT_LIBRARY

class M3UChannel:
    """Represents a single channel from an M3U playlist."""
    
    def __init__(self, name, url, group="", logo="", epg_id="", duration=-1):
        self.name = name
        self.url = url
        self.group = group or "Uncategorized"
        self.logo = logo
        self.epg_id = epg_id
        self.duration = duration
    
    def __str__(self):
        return f"{self.name} ({self.group})"

class M3UParser(QObject):
    """M3U Companion - Parses M3U playlists from URLs or files."""
    
    # Signals for progress updates
    progress_update = pyqtSignal(str)
    parsing_finished = pyqtSignal(list, dict)  # channels, groups
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.channels = []
        self.groups = {}
    
    def parse_from_url(self, url):
        """M3U Companion - Load and parse M3U playlist from URL."""
        try:
            self.progress_update.emit("Downloading M3U playlist...")
            
            headers = {
                'User-Agent': 'M3UCompanion/1.0',
                'Accept': 'application/x-mpegURL, text/plain, */*'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Try to decode with different encodings
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    content = response.content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("Unable to decode playlist content")
            
            self.progress_update.emit("Parsing M3U playlist...")
            self._parse_content(content)
            
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Failed to download playlist: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Error parsing playlist: {str(e)}")
    
    def parse_from_file(self, file_path):
        """M3U Companion - Load and parse M3U playlist from local file."""
        try:
            self.progress_update.emit("Reading M3U file...")
            
            # Try to read with different encodings
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("Unable to decode file content")
            
            self.progress_update.emit("Parsing M3U file...")
            self._parse_content(content)
            
        except FileNotFoundError:
            self.error_occurred.emit("M3U file not found")
        except Exception as e:
            self.error_occurred.emit(f"Error reading file: {str(e)}")
    
    def _parse_content(self, content):
        """Parse M3U content and extract channels with optimized performance."""
        self.channels = []
        self.groups = {}
        
        lines = content.strip().split('\n')
        current_info = {}
        total_lines = len(lines)
        
        # Batch processing for better performance
        batch_size = 100
        processed = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith('#EXTM3U'):
                continue
            elif line.startswith('#EXTINF:'):
                # Parse EXTINF line
                current_info = self._parse_extinf_line(line)
            elif line.startswith('#EXTGRP:'):
                # Group information
                current_info['group'] = line.replace('#EXTGRP:', '').strip()
            elif line.startswith('#') or line.startswith('//'):
                # Skip other comments
                continue
            elif line.startswith(('http', 'rtmp', 'rtsp', 'udp', 'rtp')):
                # This is a stream URL
                if current_info:
                    channel = M3UChannel(
                        name=current_info.get('name', f'Channel {len(self.channels) + 1}'),
                        url=line,
                        group=current_info.get('group', 'Uncategorized'),
                        logo=current_info.get('logo', ''),
                        epg_id=current_info.get('epg_id', ''),
                        duration=current_info.get('duration', -1)
                    )
                    self.channels.append(channel)
                    
                    # Add to groups efficiently
                    group_name = channel.group
                    if group_name not in self.groups:
                        self.groups[group_name] = []
                    self.groups[group_name].append(channel)
                
                current_info = {}  # Reset for next channel
                processed += 1
                
                # Emit progress updates in batches for better performance
                if processed % batch_size == 0:
                    progress = int((i / total_lines) * 100)
                    self.progress_update.emit(f"Processing... {progress}% ({processed} channels found)")
        
        self.progress_update.emit(f"✅ Parsed {len(self.channels)} channels in {len(self.groups)} groups")
        self.parsing_finished.emit(self.channels, self.groups)
    
    def _parse_extinf_line(self, line):
        """Parse EXTINF line to extract channel information."""
        info = {}
        
        # Extract duration
        duration_match = re.search(r'#EXTINF:(-?\d+(?:\.\d+)?)', line)
        if duration_match:
            info['duration'] = float(duration_match.group(1))
        
        # Extract attributes
        # tvg-id
        tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
        if tvg_id_match:
            info['epg_id'] = tvg_id_match.group(1)
        
        # tvg-logo
        logo_match = re.search(r'tvg-logo="([^"]*)"', line)
        if logo_match:
            info['logo'] = logo_match.group(1)
        
        # group-title
        group_match = re.search(r'group-title="([^"]*)"', line)
        if group_match:
            info['group'] = group_match.group(1)
        
        # Channel name (everything after the last comma)
        name_match = re.search(r',(.+?)$', line)
        if name_match:
            info['name'] = name_match.group(1).strip()
        
        return info
    
    def get_channels_by_group(self, group_name):
        """Get all channels in a specific group."""
        return self.groups.get(group_name, [])
    
    def search_channels(self, query):
        """Search channels by name."""
        query = query.lower()
        return [channel for channel in self.channels 
                if query in channel.name.lower() or query in channel.group.lower()]
    
    def get_group_names(self):
        """Get list of all group names."""
        return sorted(self.groups.keys())
    
    def get_channel_count(self):
        """Get total number of channels."""
        return len(self.channels)
    
    def clear(self):
        """Clear all parsed data."""
        self.channels = []
        self.groups = {}
