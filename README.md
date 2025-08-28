# 📺 IPTV Companion Suite

**A comprehensive cross-platform IPTV management solution featuring two powerful applications for all your streaming needs.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)](https://github.com/yourusername/IPTV-Companion)

---

## 🚀 Quick Start

### **Windows Users (Recommended)**
1. Download the latest executables from **[Releases](https://github.com/yourusername/IPTV-Companion/releases)**
2. Run `M3U-Companion.exe` or `Xtream-Companion.exe` - **No installation required!**

### **Linux Users**
```bash
# Clone the repository
git clone https://github.com/yourusername/IPTV-Companion.git
cd IPTV-Companion

# Choose your application
cd M3U-Companion    # or cd Xtream-Companion

# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the application
python src/main.py
```

---

## 📱 Applications Overview

| Feature | M3U Companion | Xtream Companion |
|---------|---------------|------------------|
| **Purpose** | M3U/M3U8 Playlist Viewer | Xtream Codes Account Manager |
| **Input** | M3U files/URLs | Xtream server credentials |
| **Best For** | Local playlists, file-based IPTV | Professional IPTV services |
| **Key Feature** | Advanced playlist parsing | Real-time account validation |

---

## 🎬 M3U Companion

**Modern M3U playlist viewer with seamless media player integration**

### ✨ Key Features
- **📁 Dual Input Support** - Load from URLs or local files
- **🎨 Modern UI** - Dark theme with smooth animations (PySide6/PyQt6)
- **🔍 Smart Search** - Real-time channel filtering
- **📺 Media Players** - FFplay & MPV integration with auto-detection
- **🌍 Cross-Platform** - Windows, Linux, macOS support
- **⚡ Performance** - Multi-threaded loading for large playlists

### 🛠️ Usage
1. **Launch M3U Companion**
2. **Load Playlist:**
   - Click **"🌐 Load from URL"** and enter M3U URL
   - Or click **"📁 Load from File"** to browse local files
3. **Browse Channels:**
   - Select groups from left panel
   - Use search box to filter channels
   - Click **"▶️ Play"** to stream

### 📋 Supported Formats
```m3u
#EXTM3U
#EXTINF:-1 tvg-id="news1" tvg-logo="logo.png" group-title="News",News Channel
http://example.com/stream.m3u8
```

---

## 🔐 Xtream Companion

**Professional Xtream Codes account manager with built-in playlist viewer**

### ✨ Key Features
- **✅ Account Validation** - Real-time status checking (Active/Expired/Banned)
- **📊 Bulk Processing** - Check multiple accounts simultaneously
- **📺 Integrated Viewer** - Built-in playlist browser for active accounts
- **📡 EPG Support** - "Now Playing" information display
- **🎯 API Direct** - Communicates directly with Xtream Codes API
- **🚀 High Performance** - Multi-threaded with lazy loading

### 🛠️ Usage
1. **Launch Xtream Companion**
2. **Add Accounts:**
   - Enter server URL, username, password
   - Or import from file (bulk checking)
3. **Check Status:**
   - Click **"Check Accounts"** for validation
   - View results with color-coded status
4. **Browse Active Accounts:**
   - Double-click active accounts to open playlist viewer
   - Browse channels with EPG information

---

## 🔧 Installation & Setup

### **System Requirements**
- **Python 3.8+** (for source installation)
- **FFmpeg** or **MPV** (for media playback)
- **Windows 10+** or **Linux** (Ubuntu 18.04+)

### **Dependencies Installation**

**Windows:**
```powershell
# Install FFmpeg (recommended)
winget install Gyan.FFmpeg

# Or install MPV
winget install mpv.net
```

**Linux (Ubuntu/Debian):**
```bash
# Install FFmpeg
sudo apt update
sudo apt install ffmpeg

# Or install MPV
sudo apt install mpv
```

### **Python Dependencies**
Both applications use the same core dependencies:
```txt
PyQt6>=6.4.0
PySide6>=6.4.0
requests>=2.28.0
urllib3>=1.26.0
```

---

## 🛠️ Building from Source

### **Prerequisites**
```bash
pip install pyinstaller
```

### **Build M3U Companion**
```bash
cd M3U-Companion
python build.py
```

### **Build Xtream Companion**
```bash
cd Xtream-Companion
python build.py
```

**Output:** Standalone executables in `dist/` folder

---

## 🐛 Troubleshooting

### **Common Issues**

| Issue | Solution |
|-------|----------|
| **"Player not found"** | Install FFmpeg or MPV, ensure they're in PATH |
| **"URL timeout"** | Check internet connection and URL validity |
| **"Import failed"** | Verify file format and encoding (UTF-8 recommended) |
| **"API error"** | Confirm Xtream server URL and credentials |
| **"Qt library error"** | Install missing Qt dependencies: `pip install PyQt6 PySide6` |

### **Performance Tips**
- **Large playlists:** Use search to filter channels
- **Slow loading:** Check internet connection for URL-based playlists
- **Memory usage:** Close unused playlist viewers

---

## 🏗️ Architecture

### **M3U Companion**
```
src/
├── main.py              # Application entry point
├── ui.py                # Modern UI with animations
├── m3u_parser.py        # M3U parsing engine
├── media_player.py      # Player integration
├── qt_compatibility.py  # Cross-platform Qt support
├── error_handler.py     # Error management
└── ui_animations.py     # UI effects & animations
```

### **Xtream Companion**
```
src/
├── main.py              # Application entry point
├── ui.py                # Account management UI
├── checker.py           # Xtream API client
├── m3u_parser.py        # Playlist parsing
├── media_player.py      # Player integration
└── qt_compatibility.py  # Cross-platform support
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** Pull Request

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## ❤️ Acknowledgments

- **PyQt6/PySide6** - Excellent cross-platform GUI framework
- **FFmpeg & MPV** - Reliable media playback engines
- **Python Community** - Outstanding ecosystem and libraries
- **Contributors** - Testing, feedback, and improvements

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/IPTV-Companion/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/IPTV-Companion/discussions)
- **Wiki:** [Documentation](https://github.com/yourusername/IPTV-Companion/wiki)

---

<div align="center">

**🌟 Star this repository if you find it helpful! 🌟**

Made with ❤️ for the IPTV community

</div>
