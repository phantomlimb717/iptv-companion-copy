"""
M3U playlist parser for handling both local files and remote URLs.
Supports extended M3U format with metadata parsing.
"""
import re
import requests
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Union
import os

class M3UChannel:
    """Represents a single channel/stream from an M3U playlist"""
    
    def __init__(self, name: str, url: str, group: str = "", logo: str = "", tvg_id: str = "", 
                 tvg_name: str = "", duration: int = -1, additional_info: Dict = None):
        self.name = name
        self.url = url
        self.group = group or "Uncategorized"
        self.logo = logo
        self.tvg_id = tvg_id
        self.tvg_name = tvg_name
        self.duration = duration
        self.additional_info = additional_info or {}
    
    def __repr__(self):
        return f"M3UChannel(name='{self.name}', group='{self.group}', url='{self.url[:50]}...')"

class M3UPlaylist:
    """Represents a complete M3U playlist with channels organized by groups"""
    
    def __init__(self, source: str = ""):
        self.source = source
        self.channels: List[M3UChannel] = []
        self.groups: Dict[str, List[M3UChannel]] = {}
        self.metadata: Dict = {}
    
    def add_channel(self, channel: M3UChannel):
        """Add a channel to the playlist"""
        self.channels.append(channel)
        
        # Organize by group
        if channel.group not in self.groups:
            self.groups[channel.group] = []
        self.groups[channel.group].append(channel)
    
    def get_groups(self) -> List[str]:
        """Get all group names sorted alphabetically"""
        return sorted(self.groups.keys())
    
    def get_channels_by_group(self, group_name: str) -> List[M3UChannel]:
        """Get all channels in a specific group"""
        return self.groups.get(group_name, [])
    
    def get_channel_count(self) -> int:
        """Get total number of channels"""
        return len(self.channels)
    
    def get_group_count(self) -> int:
        """Get total number of groups"""
        return len(self.groups)

class M3UParser:
    """Parser for M3U playlist files and URLs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'M3UChecker/1.0 (Cross-Platform M3U Parser)'
        })
    
    def parse_from_url(self, url: str, timeout: int = 30) -> Union[M3UPlaylist, Dict]:
        """Parse M3U playlist from a remote URL"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Try to decode with UTF-8, fallback to latin-1
            try:
                content = response.content.decode('utf-8')
            except UnicodeDecodeError:
                content = response.content.decode('latin-1', errors='ignore')
            
            playlist = self._parse_content(content, url)
            playlist.source = url
            return playlist
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to download M3U from URL: {str(e)}"}
        except Exception as e:
            return {"error": f"Error parsing M3U from URL: {str(e)}"}
    
    def parse_from_file(self, file_path: str) -> Union[M3UPlaylist, Dict]:
        """Parse M3U playlist from a local file"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Try multiple encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {"error": "Could not decode file with any supported encoding"}
            
            playlist = self._parse_content(content, file_path)
            playlist.source = file_path
            return playlist
            
        except Exception as e:
            return {"error": f"Error reading M3U file: {str(e)}"}
    
    def _parse_content(self, content: str, source: str = "") -> M3UPlaylist:
        """Parse M3U content from string"""
        playlist = M3UPlaylist(source)
        lines = content.strip().split('\n')
        
        # Check if it's an extended M3U
        is_extended = lines and lines[0].strip().upper() == '#EXTM3U'
        
        current_info = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line or line.startswith('#EXTM3U'):
                continue
            
            if line.startswith('#EXTINF:'):
                # Parse EXTINF line
                current_info = self._parse_extinf_line(line)
            elif line.startswith('#'):
                # Other metadata lines
                self._parse_metadata_line(line, current_info)
            elif line and not line.startswith('#'):
                # This is a URL line
                channel_name = current_info.get('name', self._extract_name_from_url(line))
                
                # Create channel object
                channel = M3UChannel(
                    name=channel_name,
                    url=self._resolve_url(line, source),
                    group=current_info.get('group', 'Uncategorized'),
                    logo=current_info.get('logo', ''),
                    tvg_id=current_info.get('tvg_id', ''),
                    tvg_name=current_info.get('tvg_name', ''),
                    duration=current_info.get('duration', -1),
                    additional_info=current_info.copy()
                )
                
                playlist.add_channel(channel)
                current_info = {}  # Reset for next channel
        
        return playlist
    
    def _parse_extinf_line(self, line: str) -> Dict:
        """Parse an EXTINF line and extract metadata"""
        info = {}
        
        # Extract duration and title
        # Format: #EXTINF:duration,title
        match = re.match(r'#EXTINF:\s*([^,]*),\s*(.*)', line)
        if match:
            duration_str, title_part = match.groups()
            
            # Parse duration
            try:
                info['duration'] = int(float(duration_str))
            except (ValueError, TypeError):
                info['duration'] = -1
            
            # Extract attributes from title part
            # Look for tvg-* and group-title attributes
            attr_pattern = r'(\w+(?:-\w+)*)="([^"]*)"'
            attributes = dict(re.findall(attr_pattern, title_part))
            
            # Map common attributes
            if 'tvg-id' in attributes:
                info['tvg_id'] = attributes['tvg-id']
            if 'tvg-name' in attributes:
                info['tvg_name'] = attributes['tvg-name']
            if 'tvg-logo' in attributes:
                info['logo'] = attributes['tvg-logo']
            if 'group-title' in attributes:
                info['group'] = attributes['group-title']
            
            # Extract channel name (everything after the last comma that's not an attribute)
            name_match = re.search(r',\s*([^,]*?)(?:\s+\w+(?:-\w+)*="[^"]*")*\s*$', line)
            if name_match:
                potential_name = name_match.group(1).strip()
                # Remove any remaining attributes from the name
                clean_name = re.sub(r'\s+\w+(?:-\w+)*="[^"]*"', '', potential_name).strip()
                if clean_name:
                    info['name'] = clean_name
            
            # If no clean name found, use the whole title part minus attributes
            if 'name' not in info:
                clean_title = re.sub(r'\w+(?:-\w+)*="[^"]*"', '', title_part).strip()
                info['name'] = clean_title if clean_title else "Unknown Channel"
        
        return info
    
    def _parse_metadata_line(self, line: str, current_info: Dict):
        """Parse other metadata lines"""
        # Handle other common M3U metadata
        if line.startswith('#EXTGRP:'):
            current_info['group'] = line[8:].strip()
        elif line.startswith('#EXTVLCOPT:'):
            # VLC options - store as additional info
            if 'vlc_options' not in current_info:
                current_info['vlc_options'] = []
            current_info['vlc_options'].append(line[11:].strip())
    
    def _extract_name_from_url(self, url: str) -> str:
        """Extract a reasonable name from URL if no name is provided"""
        try:
            parsed = urlparse(url)
            path = parsed.path
            
            # Try to get filename from path
            if path and path != '/':
                name = os.path.basename(path)
                if name and '.' in name:
                    name = os.path.splitext(name)[0]
                if name:
                    return name.replace('_', ' ').replace('-', ' ').title()
            
            # Fallback to hostname
            if parsed.netloc:
                return f"Stream from {parsed.netloc}"
            
        except Exception:
            pass
        
        return "Unknown Stream"
    
    def _resolve_url(self, url: str, base_source: str) -> str:
        """Resolve relative URLs against the base source"""
        if url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            return url
        
        # If source is a URL, resolve relative URLs
        if base_source.startswith(('http://', 'https://')):
            return urljoin(base_source, url)
        
        # If source is a file path, resolve relative to file directory
        if os.path.isfile(base_source):
            base_dir = os.path.dirname(base_source)
            return os.path.join(base_dir, url)
        
        return url
    
    def validate_m3u_content(self, content: str) -> Dict:
        """Validate if content appears to be a valid M3U playlist"""
        lines = content.strip().split('\n')
        
        if not lines:
            return {"valid": False, "error": "Empty content"}
        
        # Check for M3U header (optional but recommended)
        has_header = lines[0].strip().upper() == '#EXTM3U'
        
        # Count URLs and EXTINF entries
        url_count = 0
        extinf_count = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                extinf_count += 1
            elif line and not line.startswith('#'):
                # Potential URL
                if any(line.startswith(proto) for proto in ['http://', 'https://', 'rtmp://', 'rtsp://', 'file://']):
                    url_count += 1
                elif '.' in line:  # Might be a relative path
                    url_count += 1
        
        if url_count == 0:
            return {"valid": False, "error": "No valid URLs found"}
        
        return {
            "valid": True,
            "has_header": has_header,
            "url_count": url_count,
            "extinf_count": extinf_count,
            "is_extended": extinf_count > 0
        }

def test_m3u_parser():
    """Test function for M3U parser"""
    # Test with a sample M3U content
    sample_m3u = """#EXTM3U
#EXTINF:-1 tvg-id="cnn" tvg-name="CNN" tvg-logo="http://example.com/cnn.png" group-title="News",CNN International
http://example.com/cnn.m3u8
#EXTINF:-1 group-title="Entertainment",HBO
http://example.com/hbo.m3u8
#EXTINF:-1,Discovery Channel
http://example.com/discovery.m3u8"""
    
    parser = M3UParser()
    playlist = parser._parse_content(sample_m3u)
    
    print(f"Parsed {playlist.get_channel_count()} channels in {playlist.get_group_count()} groups")
    for group in playlist.get_groups():
        channels = playlist.get_channels_by_group(group)
        print(f"Group '{group}': {len(channels)} channels")
        for channel in channels:
            print(f"  - {channel.name} ({channel.url})")

if __name__ == "__main__":
    test_m3u_parser()
