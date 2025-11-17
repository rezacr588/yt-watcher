# YouTube Watcher - Web UI

Beautiful, modern web interface for controlling and monitoring YouTube watchers.

## 🎨 Features

### Control Panel
- ✅ Configure video URL
- ✅ Set number of watchers (1-50)
- ✅ Toggle headless mode
- ✅ Adjust watch percentage (min/max)
- ✅ Enable/disable proxy rotation
- ✅ Choose proxy rotation mode (random, round-robin, sticky)

### Real-Time Monitoring
- ✅ Live status updates via WebSocket
- ✅ Individual watcher cards showing:
  - Status (initializing, running, completed, failed)
  - Watching strategy
  - Proxy information
  - Progress bar
- ✅ Overall statistics:
  - Total watchers
  - Successful completions
  - Failed attempts
  - Elapsed time
- ✅ Status message feed with timestamps

### Modern Design
- 🎨 Dark theme with gradient accents
- 📱 Fully responsive (mobile-friendly)
- ⚡ Real-time updates (no page refresh)
- 🎭 Smooth animations
- 🎯 Intuitive controls

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/aiqlick/yt-watcher
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the UI Server

```bash
python app.py
```

You'll see:
```
Starting YouTube Watcher UI...
Open http://localhost:5000 in your browser
 * Running on http://0.0.0.0:5000
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

## 📖 Usage Guide

### Starting Watchers

1. **Enter Video URL**
   - Paste YouTube video URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)

2. **Configure Settings**
   - **Number of Watchers**: How many browser instances to launch (1-50)
   - **Headless Mode**: Run browsers without GUI (faster, lower resource usage)
   - **Min/Max Watch %**: Percentage of video each watcher should watch
     - Example: 0.7 to 1.0 = watch 70-100% of video
   - **Use Proxies**: Enable proxy rotation (requires proxies.txt)
   - **Proxy Rotation**: Choose rotation strategy

3. **Click "▶️ Start Watchers"**
   - Watchers will launch with staggered delays
   - Each watcher appears as a card in the grid
   - Status updates in real-time

### Monitoring

**Status Cards** show:
- **Running**: Current state (Running/Idle)
- **Total Watchers**: Number of instances
- **Successful**: Completed watchers
- **Failed**: Failed watchers
- **Elapsed Time**: Time since start

**Watcher Cards** display:
- **ID**: Watcher number
- **Status Badge**: Current state with color coding
  - 🟡 Initializing (yellow)
  - 🔵 Running (blue, pulsing)
  - 🟢 Completed (green)
  - 🔴 Failed/Error (red)
  - ⚪ Cancelled (gray)
- **Strategy**: Watching pattern (casual, engaged, quick, binge)
- **Message**: Current activity
- **Proxy**: IP/proxy being used
- **Progress Bar**: Visual progress indicator

**Status Feed** shows:
- Timestamped messages
- Color-coded by type (info/success/error)
- Auto-scrolls to latest
- Keeps last 50 messages

### Stopping Watchers

Click **"⏹️ Stop All"** to:
- Cancel all running watchers
- Clean up browser instances
- Reset for next run

## 🎛️ Configuration Options

### Video Settings
- **video_url**: Target YouTube video
- **num_browsers**: Number of simultaneous watchers (1-50)

### Behavior Settings
- **headless**: Run without browser GUI
  - `true`: Faster, less resources
  - `false`: See browsers in action

- **min_watch_percentage**: Minimum watch time (0.0-1.0)
- **max_watch_percentage**: Maximum watch time (0.0-1.0)

### Proxy Settings
- **use_proxy**: Enable proxy rotation
- **proxy_rotation**: Strategy
  - `random`: Pick random proxy for each
  - `round-robin`: Cycle through proxies
  - `sticky`: All use same proxy

## 🌐 API Endpoints

The Flask backend provides these REST endpoints:

### GET /api/config
Returns current configuration
```json
{
  "video_url": "https://youtube.com/watch?v=...",
  "num_browsers": 10,
  "headless": false,
  "min_watch_percentage": 0.7,
  "max_watch_percentage": 1.0,
  "use_proxy": false,
  "proxy_rotation": "random"
}
```

### GET /api/status
Returns current watcher status
```json
{
  "is_running": true,
  "start_time": "2025-11-17T21:45:00",
  "elapsed_seconds": 45,
  "total_watchers": 10,
  "successful": 3,
  "failed": 0,
  "watchers": [...]
}
```

### POST /api/start
Start watchers with configuration
```json
{
  "video_url": "https://youtube.com/watch?v=...",
  "num_browsers": 5,
  "headless": true,
  "min_watch_percentage": 0.7,
  "max_watch_percentage": 1.0,
  "use_proxy": false,
  "proxy_rotation": "random"
}
```

### POST /api/stop
Stop all running watchers

## 🔌 WebSocket Events

Real-time updates via Socket.IO:

### Client → Server
- `connect`: Client connected
- `disconnect`: Client disconnected
- `request_status`: Request status update

### Server → Client
- `status`: Status message
  ```json
  {
    "message": "Testing proxies...",
    "type": "info"
  }
  ```

- `watcher_update`: Individual watcher update
  ```json
  {
    "id": 0,
    "status": "running",
    "progress": 45,
    "message": "Watching video...",
    "strategy": "engaged_viewer",
    "proxy": "proxy1.com:8080"
  }
  ```

- `status_update`: Overall status update

## 📁 Architecture

```
UI Components:
├── app.py                      # Flask server & SocketIO
├── watcher_controller.py       # Manages watcher instances
├── templates/
│   └── index.html             # HTML template
├── static/
│   ├── css/
│   │   └── style.css          # Modern dark theme
│   └── js/
│       └── app.js             # Frontend logic & WebSocket
```

**Data Flow:**
```
Browser (UI) ←→ WebSocket ←→ Flask Server ←→ WatcherController
                                                      ↓
                                              YouTubeWatcher Instances
                                                      ↓
                                              Browser Automation
```

## 🎨 UI Components

### Color Scheme
- **Primary**: Blue (#2563eb) - Actions, running states
- **Success**: Green (#10b981) - Completed watchers
- **Danger**: Red (#ef4444) - Errors, failures
- **Warning**: Orange (#f59e0b) - Warnings, initializing
- **Background**: Dark slate (#0f172a, #1e293b)

### Responsive Design
- **Desktop**: Multi-column grid layout
- **Tablet**: 2-column layout
- **Mobile**: Single column, stacked

### Status Colors
- 🟡 **Initializing**: Amber warning
- 🔵 **Running**: Blue with pulse animation
- 🟢 **Completed**: Green success
- 🔴 **Failed/Error**: Red danger
- ⚪ **Cancelled**: Gray neutral

## 🔒 Security Notes

- UI runs on `0.0.0.0:5000` (accessible from network)
- No authentication (add if exposing publicly)
- CORS enabled for all origins
- WebSocket connections allowed from all origins

**For production:**
1. Change `SECRET_KEY` in app.py
2. Add authentication
3. Restrict CORS origins
4. Use HTTPS with reverse proxy (nginx)
5. Set proper firewall rules

## 🚨 Important Warnings

This UI makes it **easy** to launch many watchers, but remember:

- ⚠️ **Violates YouTube ToS**
- ⚠️ **Can result in bans**
- ⚠️ **Resource intensive** (RAM/CPU)
- ⚠️ **For education only**

**Recommended limits:**
- Start with 1-5 watchers to test
- Monitor system resources
- Use headless mode for better performance
- Test on your own videos first

## 🐛 Troubleshooting

### Port Already in Use
```
Error: Address already in use
```
**Solution**: Change port in app.py or kill process using 5000

### WebSocket Connection Failed
```
WebSocket error in browser console
```
**Solution**:
- Check Flask server is running
- Check firewall allows port 5000
- Refresh browser page

### Watchers Not Starting
```
Error message in status feed
```
**Solution**:
- Check video URL is valid
- Verify .env configuration
- Check logs in terminal
- Ensure Playwright installed: `playwright install chromium`

### High Resource Usage
```
System slowing down
```
**Solution**:
- Reduce number of watchers
- Enable headless mode
- Increase launch delays
- Close other applications

## 📊 Performance Tips

1. **Use Headless Mode**
   - Saves GPU/RAM
   - Faster execution
   - Better for high counts

2. **Stagger Launches**
   - Configured automatically
   - Reduces system spike
   - More natural pattern

3. **Monitor Resources**
   - Each watcher: ~200-300MB RAM
   - 10 watchers: ~2-3GB RAM
   - CPU usage varies by system

4. **Optimal Settings**
   - Development: 1-5 watchers, headless=false
   - Testing: 5-10 watchers, headless=true
   - Max tested: 50 watchers (requires 8GB+ RAM)

## 🎯 Next Steps

After starting the UI:

1. **Test with 1 watcher first**
   - Verify configuration works
   - Check browser launches
   - Confirm video plays

2. **Gradually increase**
   - Try 5 watchers
   - Monitor system resources
   - Adjust settings as needed

3. **Add proxies (optional)**
   - Create proxies.txt
   - Enable "Use Proxies"
   - Watch proxy status in UI

4. **Monitor logs**
   - Terminal shows detailed logs
   - UI shows user-friendly messages
   - Check youtube_watcher.log file

## 📚 Related Files

- [README.md](README.md) - Main project documentation
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview
- [.env.example](.env.example) - Configuration template

---

**Built with**: Flask, Socket.IO, Vanilla JavaScript, Modern CSS
**Status**: ✅ Production Ready
**UI Version**: 1.0.0
