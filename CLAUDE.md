# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Watcher is an educational browser automation tool demonstrating advanced anti-detection techniques, human-like behavior simulation, and comprehensive testing practices. **Educational purposes only - violates YouTube ToS.**

## Essential Commands

### Development Setup
```bash
# Virtual environment setup
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
playwright install chromium

# Configuration
cp .env.example .env
# Edit .env with VIDEO_URL and other settings
```

### Running the Application

**Web UI (Recommended):**
```bash
python app.py
# Then open http://localhost:5001
# Or use: ./start_ui.sh
```

**Command Line:**
```bash
python youtube_watcher.py
```

### Testing

```bash
# Run all tests (102 tests)
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests
pytest -m e2e            # End-to-end tests
pytest -m "not slow"     # Skip slow tests

# Run single test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::TestConfig::test_default_values

# Verbose output
pytest -vv
```

### Quick Application Test
```bash
python test_run.py  # Tests imports and basic initialization
```

## Architecture

### Two-Mode System

**1. Web UI Mode (Flask + SocketIO)**
- Modern web interface at http://localhost:5001
- Real-time WebSocket updates
- Visual monitoring of each watcher
- Live progress tracking
- Files: `app.py`, `watcher_controller.py`, `templates/`, `static/`

**2. Command-Line Mode**
- Direct execution via `youtube_watcher.py`
- Standalone operation
- Useful for scripting and automation

### Core Module Interaction Flow

```
YouTubeWatcher (main orchestrator)
    ↓
    ├─→ Config (environment variables, validation)
    ├─→ ProxyManager (rotation, health checks)
    ├─→ BehaviorPatterns (human simulation)
    └─→ StealthConfig (anti-detection)
```

### Web UI Architecture

```
Browser/User
    ↓ (WebSocket)
Flask App (app.py)
    ↓ (thread-local event loops)
WatcherController (watcher_controller.py)
    ↓ (async tasks with callbacks)
YouTubeWatcher instances
    ↓ (progress_callback)
Real-time UI updates
```

**Critical Implementation Details:**

1. **Thread-Local Event Loops**: Flask runs in threaded mode. Each thread gets its own asyncio event loop via `threading.local()` to avoid race conditions.

2. **Progress Callbacks**: Watchers are injected with `progress_callback` function that emits WebSocket updates during execution phases:
   - Browser setup
   - Navigation
   - Video watching (every 10-25 seconds)
   - Completion

3. **SocketIO Callback Pattern**: Controller uses `socketio_callback(event_type, data)` to emit events from background threads to connected clients.

### Key Components

**youtube_watcher.py (257 lines)**
- Main automation class
- Manages Playwright browser lifecycle
- **Important**: Now stores `self.playwright` instance and calls `await self.playwright.stop()` in cleanup to prevent resource leaks
- Executes behavior patterns
- Handles retries (3 attempts by default)
- **New**: Accepts `progress_callback` for real-time UI updates

**watcher_controller.py (218 lines)**
- Manages multiple watcher instances
- Tracks status for UI display
- Runs watchers in asyncio tasks
- **New**: Injects progress callbacks into watchers for real-time updates
- Handles concurrent watcher execution
- Provides status API for UI

**config.py (48 lines)**
- Centralized configuration via environment variables
- Validation logic (ranges, file existence)
- All settings accessible as class attributes
- **Updated**: Default VIDEO_URL is now `https://www.youtube.com/watch?v=R71Rh1HR7Js`

**proxy_manager.py (153 lines)**
- `Proxy` dataclass for proxy representation
- `ProxyManager` for rotation logic
- `ProxyPool` singleton for global access
- Supports HTTP, HTTPS, SOCKS5 with authentication
- Three rotation modes: random, round-robin, sticky
- Health checking via concurrent async tests

**behavior_patterns.py (163 lines)**
- Bezier curve mouse movements (cubic interpolation)
- Beta distribution for human-like timing delays
- Four watching strategies: casual, engaged, quick, binge
- Interaction probabilities from Config
- Random behavior sequences per session

**stealth.py (45 lines)**
- JavaScript injection to hide `navigator.webdriver`
- Canvas/audio fingerprint randomization
- Plugin/language/permissions mocking
- Browser launch arguments for anti-detection
- User agent rotation from `fake-useragent`

**app.py (143 lines)**
- Flask server on port 5001
- SocketIO for real-time bidirectional communication
- **Critical**: Uses `threading.local()` for event loops (not global variable)
- REST endpoints: `/api/config`, `/api/status`, `/api/start`, `/api/stop`
- WebSocket events: `status`, `watcher_update`, `status_update`

### Testing Architecture

**Test Strategy:**
- **Unit tests**: Mock external dependencies (browser, network)
- **Integration tests**: Test component interaction with partial mocking
- **E2E tests**: Test complete workflows with full mocking

**Key Testing Patterns:**
- `AsyncMock` for Playwright browser/page objects
- `pytest-asyncio` for async test functions
- `pytest.fixture` with appropriate scopes (function, session)
- Coverage excludes browser-specific code that requires real Playwright

**test_stealth.py Note**: Uses partial string matching (e.g., `assert 'plugins' in js`) instead of exact matches to accommodate JavaScript minification variations.

## Important Implementation Notes

### Playwright Resource Management
- **Always** store Playwright instance: `self.playwright = await async_playwright().start()`
- **Always** cleanup: `await self.playwright.stop()` in cleanup method
- Without proper cleanup, Playwright instances leak resources

### Thread Safety in Flask
- Use `threading.local()` for per-thread event loops
- Never use global event loop variables with Flask's threaded mode
- Each request thread needs its own asyncio event loop

### Real-Time Updates
- Watchers report progress via `self.progress_callback(message, progress)`
- Progress ranges: 0-10 (setup), 10-30 (navigation), 30-90 (watching), 90-100 (completion)
- UI cards update every 10-25 seconds during video watching

### Configuration Precedence
1. Environment variables in `.env` file (active config)
2. Fallback defaults in `config.py`
3. UI overrides via `/api/start` endpoint

### Proxy Format
```
protocol://[username:password@]host:port

Examples:
http://proxy.com:8080
socks5://user:pass@proxy.com:1080
```

## Common Development Tasks

### Adding New Behavior Pattern
1. Add function to `behavior_patterns.py`
2. Update `BEHAVIOR_TYPES` list
3. Add probability to `Config` if needed
4. Write unit test in `test_behavior_patterns.py`
5. Test in integration test

### Adding Real-Time Progress Point
1. In `youtube_watcher.py`, add:
   ```python
   if self.progress_callback:
       await self.progress_callback("Status message", progress_percentage)
   ```
2. Progress should be 0-100 integer
3. Updates appear in UI watcher cards instantly

### Modifying Configuration
1. Add environment variable to `.env.example`
2. Add class attribute to `Config` in `config.py`
3. Add validation in `Config.validate()` if needed
4. Write test in `test_config.py`
5. Document in README.md

### Running Without Playwright Browsers
If you need to test code without browser automation:
```bash
# Skip e2e tests that would require browsers
pytest -m "not e2e"
```

## Debugging Tips

### View Browser Automation
Set `HEADLESS=false` in `.env` or uncheck "Headless Mode" in UI to see browser windows.

### Monitor WebSocket Events
Open browser DevTools → Network → WS → Click socket connection → Messages tab to see real-time events.

### Check Background Flask Logs
When UI is running, Flask logs show in terminal including WebSocket emissions and errors.

### Test Single Watcher
In UI, set "Number of Watchers" to 1 and uncheck headless to debug single browser instance.

## File Organization

```
yt-watcher/
├── Core Modules (5 files)
│   ├── youtube_watcher.py    - Main automation
│   ├── config.py             - Configuration
│   ├── proxy_manager.py      - Proxy handling
│   ├── behavior_patterns.py  - Human simulation
│   └── stealth.py           - Anti-detection
│
├── Web UI (5 files)
│   ├── app.py                      - Flask server
│   ├── watcher_controller.py       - Watcher management
│   ├── templates/index.html        - HTML interface
│   ├── static/css/style.css        - Dark theme styling
│   └── static/js/app.js            - Frontend logic
│
├── Tests (7 files, 102 tests)
│   ├── test_config.py              - 9 tests
│   ├── test_proxy_manager.py       - 20 tests
│   ├── test_behavior_patterns.py   - 16 tests
│   ├── test_stealth.py             - 18 tests
│   ├── test_youtube_watcher.py     - 13 tests
│   ├── test_integration.py         - 11 tests
│   └── test_e2e.py                 - 15 tests
│
├── Configuration
│   ├── .env                  - Active config (git-ignored)
│   ├── .env.example          - Template
│   ├── requirements.txt      - Dependencies
│   └── pytest.ini           - Test configuration
│
├── Documentation (6 files)
│   ├── README.md            - Main documentation
│   ├── PROJECT_SUMMARY.md   - Project overview
│   ├── UI_README.md         - UI documentation
│   ├── UI_FEATURES.md       - Feature list
│   ├── FINAL_REVIEW.md      - Status report
│   └── CLAUDE.md            - This file
│
└── Utilities
    ├── test_run.py          - Quick app test
    └── start_ui.sh          - UI startup script
```

## Known Issues and Fixes Applied

1. **Fixed**: Playwright resource leak - now properly stores and stops Playwright instance
2. **Fixed**: Thread safety issues - uses `threading.local()` for event loops
3. **Fixed**: Missing real-time updates - watchers now have progress callbacks
4. **Fixed**: Task cancellation handling - added async cleanup method

## Educational Value

This codebase demonstrates:
- Production-quality Python async programming
- Browser automation with Playwright
- Anti-detection techniques (educational)
- Test-driven development (87% coverage)
- Real-time web applications (WebSocket)
- Thread-safe asyncio integration with Flask
- Clean architecture and separation of concerns

## Legal and Ethical Reminders

⚠️ **This tool violates YouTube's Terms of Service**
- For educational purposes only
- Can result in account bans and legal consequences
- Only use on content you own or have permission to test
- Demonstrates techniques, not intended for production use

## Platform-Specific Notes

**macOS Optimizations:**
- Uses `open` command for browser launching
- Playwright Chromium path: `~/Library/Caches/ms-playwright/`
- Thread handling optimized for macOS's threading model

**Cross-Platform:**
- All async code uses `asyncio` (platform-independent)
- Playwright supports Windows, macOS, Linux
- Tests run on all platforms
