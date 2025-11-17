"""
Configuration module for YouTube Watcher
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings"""

    # Video settings
    VIDEO_URL = os.getenv('VIDEO_URL', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ')

    # Browser settings
    NUM_BROWSERS = int(os.getenv('NUM_BROWSERS', '10'))
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'

    # Timing settings (in seconds)
    MIN_WATCH_PERCENTAGE = float(os.getenv('MIN_WATCH_PERCENTAGE', '0.7'))  # Watch at least 70% of video
    MAX_WATCH_PERCENTAGE = float(os.getenv('MAX_WATCH_PERCENTAGE', '1.0'))  # Watch up to 100%

    LAUNCH_DELAY_MIN = float(os.getenv('LAUNCH_DELAY_MIN', '2'))
    LAUNCH_DELAY_MAX = float(os.getenv('LAUNCH_DELAY_MAX', '8'))

    ACTION_DELAY_MIN = float(os.getenv('ACTION_DELAY_MIN', '1'))
    ACTION_DELAY_MAX = float(os.getenv('ACTION_DELAY_MAX', '3'))

    # Proxy settings
    USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
    PROXY_LIST_FILE = os.getenv('PROXY_LIST_FILE', 'proxies.txt')
    PROXY_ROTATION = os.getenv('PROXY_ROTATION', 'random')  # 'random', 'round-robin', 'sticky'

    # Advanced behavior settings
    ENABLE_MOUSE_MOVEMENT = os.getenv('ENABLE_MOUSE_MOVEMENT', 'true').lower() == 'true'
    ENABLE_SCROLLING = os.getenv('ENABLE_SCROLLING', 'true').lower() == 'true'
    ENABLE_VOLUME_CHANGES = os.getenv('ENABLE_VOLUME_CHANGES', 'true').lower() == 'true'
    ENABLE_QUALITY_CHANGES = os.getenv('ENABLE_QUALITY_CHANGES', 'false').lower() == 'true'
    ENABLE_FULLSCREEN = os.getenv('ENABLE_FULLSCREEN', 'false').lower() == 'true'

    # Interaction probabilities (0.0 to 1.0)
    MOUSE_MOVEMENT_PROBABILITY = float(os.getenv('MOUSE_MOVEMENT_PROBABILITY', '0.4'))
    SCROLL_PROBABILITY = float(os.getenv('SCROLL_PROBABILITY', '0.3'))
    VOLUME_CHANGE_PROBABILITY = float(os.getenv('VOLUME_CHANGE_PROBABILITY', '0.1'))
    PAUSE_RESUME_PROBABILITY = float(os.getenv('PAUSE_RESUME_PROBABILITY', '0.05'))
    SEEK_PROBABILITY = float(os.getenv('SEEK_PROBABILITY', '0.1'))

    # User agent rotation
    ROTATE_USER_AGENTS = os.getenv('ROTATE_USER_AGENTS', 'true').lower() == 'true'

    # Geographic diversity
    RANDOM_LOCATIONS = os.getenv('RANDOM_LOCATIONS', 'true').lower() == 'true'

    # Anti-detection features
    STEALTH_MODE = os.getenv('STEALTH_MODE', 'true').lower() == 'true'
    RANDOMIZE_VIEWPORT = os.getenv('RANDOMIZE_VIEWPORT', 'true').lower() == 'true'

    # Retry settings
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = float(os.getenv('RETRY_DELAY', '5'))

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'youtube_watcher.log')

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.NUM_BROWSERS < 1:
            raise ValueError("NUM_BROWSERS must be at least 1")

        if not (0 <= cls.MIN_WATCH_PERCENTAGE <= 1):
            raise ValueError("MIN_WATCH_PERCENTAGE must be between 0 and 1")

        if not (0 <= cls.MAX_WATCH_PERCENTAGE <= 1):
            raise ValueError("MAX_WATCH_PERCENTAGE must be between 0 and 1")

        if cls.MIN_WATCH_PERCENTAGE > cls.MAX_WATCH_PERCENTAGE:
            raise ValueError("MIN_WATCH_PERCENTAGE cannot be greater than MAX_WATCH_PERCENTAGE")

        if cls.USE_PROXY and not os.path.exists(cls.PROXY_LIST_FILE):
            print(f"Warning: Proxy list file '{cls.PROXY_LIST_FILE}' not found. Proxies will be disabled.")
            cls.USE_PROXY = False

        return True
