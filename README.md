# YouTube Watcher - Advanced Browser Automation

A sophisticated YouTube video automation tool with human-like behavior patterns, proxy support, and advanced anti-detection features.

## ⚠️ LEGAL WARNING

**This tool is provided for EDUCATIONAL PURPOSES ONLY.**

- Using this tool to artificially inflate YouTube video views violates [YouTube's Terms of Service](https://www.youtube.com/t/terms)
- Artificially manipulating view counts may result in:
  - Account termination
  - IP address bans
  - Legal action
  - Removal of videos
- This tool is intended for learning about browser automation, anti-detection techniques, and distributed systems

**USE AT YOUR OWN RISK. The authors are not responsible for any misuse or consequences.**

---

## Features

### 🎭 Advanced Anti-Detection
- **Stealth Mode**: Hides automation markers (`navigator.webdriver`, etc.)
- **Fingerprint Randomization**: Randomizes canvas, audio, and WebGL fingerprints
- **User Agent Rotation**: Cycles through realistic browser user agents
- **Viewport Randomization**: Uses common screen resolutions
- **Geographic Diversity**: Simulates users from different locations

### 🎪 Human-Like Behavior
- **Natural Mouse Movement**: Bezier curve-based cursor movement
- **Realistic Scrolling**: Multiple scroll patterns (reading, scanning, etc.)
- **Video Interactions**: Pause/resume, seeking, volume adjustment
- **Watching Strategies**: Different viewer types (casual, engaged, quick, binge)
- **Random Timing**: Human-like delays between actions

### 🌐 Proxy Support
- **Multiple Protocols**: HTTP, HTTPS, SOCKS5
- **Rotation Modes**: Random, round-robin, sticky
- **Authentication**: Username/password support
- **Health Checking**: Automatic proxy validation
- **Statistics**: Track proxy usage and performance

### ⚙️ Configuration
- **Environment Variables**: Flexible configuration via `.env` file
- **Adjustable Probabilities**: Fine-tune interaction frequencies
- **Watch Time Control**: Configure min/max watch percentages
- **Retry Logic**: Automatic retry on failures

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download the repository**
   ```bash
   cd yt-watcher
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome**
   Ensure Google Chrome is installed on your system.

4. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

---

## Usage

### Basic Usage

Run with default settings:
```bash
python youtube_watcher.py
```

### Configuration

Edit `.env` file or set environment variables:

```bash
# Basic settings
VIDEO_URL=https://www.youtube.com/watch?v=YOUR_VIDEO_ID
NUM_BROWSERS=10
HEADLESS=false

# Watch time (percentage of video)
MIN_WATCH_PERCENTAGE=0.7
MAX_WATCH_PERCENTAGE=1.0

# Timing (seconds)
LAUNCH_DELAY_MIN=2
LAUNCH_DELAY_MAX=8

# Proxy settings
USE_PROXY=true
PROXY_LIST_FILE=proxies.txt
PROXY_ROTATION=random
```

### Proxy Setup

Create `proxies.txt` with one proxy per line:

```text
http://proxy1.com:8080
http://user:pass@proxy2.com:3128
socks5://proxy3.com:1080
```

Supported formats:
- `http://host:port`
- `http://username:password@host:port`
- `socks5://host:port`
- `socks5://username:password@host:port`

### Advanced Configuration

#### Behavior Probabilities (0.0 to 1.0)
```bash
MOUSE_MOVEMENT_PROBABILITY=0.4
SCROLL_PROBABILITY=0.3
VOLUME_CHANGE_PROBABILITY=0.1
PAUSE_RESUME_PROBABILITY=0.05
SEEK_PROBABILITY=0.1
```

#### Anti-Detection Features
```bash
ROTATE_USER_AGENTS=true
RANDOM_LOCATIONS=true
STEALTH_MODE=true
RANDOMIZE_VIEWPORT=true
```

---

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# End-to-end tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Test Structure
```
tests/
├── test_config.py           # Configuration tests
├── test_proxy_manager.py    # Proxy management tests
├── test_behavior_patterns.py # Behavior simulation tests
├── test_stealth.py          # Anti-detection tests
├── test_youtube_watcher.py  # Main watcher tests
├── test_integration.py      # Integration tests
└── test_e2e.py             # End-to-end tests
```

---

## Architecture

### Project Structure
```
yt-watcher/
├── config.py               # Configuration management
├── proxy_manager.py        # Proxy rotation and validation
├── behavior_patterns.py    # Human behavior simulation
├── stealth.py             # Anti-detection features
├── youtube_watcher.py     # Main watcher implementation
├── requirements.txt       # Python dependencies
├── pytest.ini            # Pytest configuration
├── .env.example          # Environment template
└── tests/                # Test suite
    ├── test_config.py
    ├── test_proxy_manager.py
    ├── test_behavior_patterns.py
    ├── test_stealth.py
    ├── test_youtube_watcher.py
    ├── test_integration.py
    └── test_e2e.py
```

### Components

#### Config Module
- Loads settings from environment variables
- Validates configuration
- Provides default values

#### Proxy Manager
- Loads proxies from file
- Rotates proxies (random, round-robin, sticky)
- Tests proxy connectivity
- Tracks usage statistics

#### Behavior Patterns
- Natural mouse movements (Bezier curves)
- Realistic scrolling patterns
- Video player interactions
- Watching strategies

#### Stealth Module
- JavaScript injection for anti-detection
- Fingerprint randomization
- Browser argument configuration
- User agent rotation

#### YouTube Watcher
- Browser setup and management
- Video navigation and playback
- Behavior execution
- Error handling and retries

---

## Performance

### Resource Usage
- **Memory**: ~200-300 MB per browser instance
- **CPU**: Varies by system and number of browsers
- **Network**: Depends on proxy and video quality

### Recommended Limits
- **Start small**: Begin with 5-10 browsers
- **Monitor resources**: Watch CPU/RAM usage
- **Adjust timing**: Increase delays if system struggles

### Optimization Tips
1. Use `HEADLESS=true` to reduce GPU usage
2. Reduce `NUM_BROWSERS` on slower systems
3. Increase `LAUNCH_DELAY` to stagger startups
4. Use local proxies for better performance

---

## Troubleshooting

### Common Issues

#### Browser Launch Failures
```
Error: Browser launch failed
```
**Solution**: Ensure Google Chrome is installed and accessible.

#### Proxy Connection Errors
```
Warning: No working proxies found
```
**Solution**:
- Verify proxy list format
- Test proxies manually
- Check firewall settings

#### Video Not Playing
```
Error: Video stopped playing
```
**Solution**:
- Check video URL is public
- Verify internet connection
- Try with `HEADLESS=false` to debug

#### High Resource Usage
```
System becoming slow
```
**Solution**:
- Reduce `NUM_BROWSERS`
- Increase delays between actions
- Use `HEADLESS=true`

---

## Best Practices

### For Testing/Learning
1. Use test videos (your own content)
2. Start with 1-2 browsers to understand behavior
3. Monitor logs to see what's happening
4. Test with `HEADLESS=false` first

### For Ethical Use
1. Only use on content you own/have permission for
2. Respect platform terms of service
3. Consider rate limiting and throttling
4. Be transparent about automation

### Security
1. Keep proxy credentials secure
2. Don't commit `.env` file to version control
3. Use reputable proxy providers
4. Monitor for suspicious activity

---

## Development

### Running Tests During Development
```bash
# Run tests in watch mode
pytest --watch

# Run with verbose output
pytest -vv

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::TestConfig::test_default_values
```

### Code Coverage
```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# View coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Adding New Features
1. Update relevant module (config, behavior, stealth, etc.)
2. Add configuration option in `config.py`
3. Write unit tests for new functionality
4. Add integration tests if multiple components involved
5. Update README with new feature documentation

---

## FAQ

**Q: Is this legal?**
A: The tool itself is legal for educational purposes. However, using it to manipulate YouTube views violates their ToS.

**Q: Will this work forever?**
A: No. Platforms continuously improve bot detection. This is a learning tool, not a production solution.

**Q: Can I get banned?**
A: Yes. Using this on YouTube can result in account bans, IP blocks, and other consequences.

**Q: How many views can I generate?**
A: This tool is not designed for large-scale view manipulation. It's for learning about automation.

**Q: Do I need proxies?**
A: Not required, but recommended for testing proxy rotation features. Multiple requests from same IP are easily detected.

**Q: Why are the tests important?**
A: Tests ensure the code works correctly, help prevent bugs, and serve as documentation of expected behavior.

---

## Contributing

This is an educational project. Contributions should focus on:
- Improving code quality
- Adding test coverage
- Better documentation
- Educational examples

**Do not contribute** features intended for:
- Large-scale view manipulation
- Bypassing security measures maliciously
- Violating platform terms of service

---

## License

This project is provided for educational purposes only. Use responsibly and ethically.

---

## Acknowledgments

- [Selenium](https://www.selenium.dev/) - Browser automation
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) - Anti-detection driver
- [pytest](https://pytest.org/) - Testing framework
- Educational resources on browser fingerprinting and automation detection

---

## Disclaimer

The authors and contributors of this project:
- Do not endorse violating any platform's Terms of Service
- Are not responsible for any misuse of this tool
- Provide this code for educational and research purposes only
- Recommend using this tool only on content you own or have explicit permission to test

**By using this tool, you agree to use it responsibly and legally.**
