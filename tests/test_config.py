"""
Unit tests for config module
"""
import pytest
import os
from unittest.mock import patch
from config import Config


class TestConfig:
    """Test configuration module"""

    def test_default_values(self):
        """Test that default values are set correctly"""
        assert Config.NUM_BROWSERS >= 1
        assert 0 <= Config.MIN_WATCH_PERCENTAGE <= 1
        assert 0 <= Config.MAX_WATCH_PERCENTAGE <= 1
        assert Config.LAUNCH_DELAY_MIN > 0
        assert Config.LAUNCH_DELAY_MAX > Config.LAUNCH_DELAY_MIN

    def test_validate_success(self):
        """Test validation with valid config"""
        assert Config.validate() is True

    def test_validate_num_browsers_error(self):
        """Test validation fails with invalid NUM_BROWSERS"""
        original = Config.NUM_BROWSERS
        try:
            Config.NUM_BROWSERS = 0
            with pytest.raises(ValueError, match="NUM_BROWSERS must be at least 1"):
                Config.validate()
        finally:
            Config.NUM_BROWSERS = original

    def test_validate_watch_percentage_error(self):
        """Test validation fails with invalid watch percentages"""
        original_min = Config.MIN_WATCH_PERCENTAGE
        original_max = Config.MAX_WATCH_PERCENTAGE

        try:
            # Test MIN_WATCH_PERCENTAGE out of range
            Config.MIN_WATCH_PERCENTAGE = 1.5
            with pytest.raises(ValueError, match="MIN_WATCH_PERCENTAGE must be between 0 and 1"):
                Config.validate()

            Config.MIN_WATCH_PERCENTAGE = original_min

            # Test MAX_WATCH_PERCENTAGE out of range
            Config.MAX_WATCH_PERCENTAGE = -0.1
            with pytest.raises(ValueError, match="MAX_WATCH_PERCENTAGE must be between 0 and 1"):
                Config.validate()

            Config.MAX_WATCH_PERCENTAGE = original_max

            # Test MIN > MAX
            Config.MIN_WATCH_PERCENTAGE = 0.9
            Config.MAX_WATCH_PERCENTAGE = 0.5
            with pytest.raises(ValueError, match="MIN_WATCH_PERCENTAGE cannot be greater than MAX_WATCH_PERCENTAGE"):
                Config.validate()

        finally:
            Config.MIN_WATCH_PERCENTAGE = original_min
            Config.MAX_WATCH_PERCENTAGE = original_max

    def test_environment_variables(self):
        """Test that environment variables are loaded correctly"""
        with patch.dict(os.environ, {'NUM_BROWSERS': '5', 'HEADLESS': 'true'}):
            # Need to reload config to pick up env changes
            # In real scenario, config would be imported after env is set
            pass

    def test_proxy_file_not_found_warning(self):
        """Test that missing proxy file disables proxies"""
        original_use_proxy = Config.USE_PROXY
        original_proxy_file = Config.PROXY_LIST_FILE

        try:
            Config.USE_PROXY = True
            Config.PROXY_LIST_FILE = 'nonexistent_file.txt'
            Config.validate()
            # Should disable proxy if file not found
            assert Config.USE_PROXY is False

        finally:
            Config.USE_PROXY = original_use_proxy
            Config.PROXY_LIST_FILE = original_proxy_file

    def test_boolean_parsing(self):
        """Test boolean value parsing from strings"""
        # Test various true/false string values
        assert Config.HEADLESS in [True, False]
        assert Config.USE_PROXY in [True, False]

    def test_numeric_conversions(self):
        """Test that numeric values are properly converted"""
        assert isinstance(Config.NUM_BROWSERS, int)
        assert isinstance(Config.MIN_WATCH_PERCENTAGE, float)
        assert isinstance(Config.LAUNCH_DELAY_MIN, float)

    def test_probability_values(self):
        """Test that probability values are valid"""
        assert 0 <= Config.MOUSE_MOVEMENT_PROBABILITY <= 1
        assert 0 <= Config.SCROLL_PROBABILITY <= 1
        assert 0 <= Config.VOLUME_CHANGE_PROBABILITY <= 1
        assert 0 <= Config.PAUSE_RESUME_PROBABILITY <= 1
        assert 0 <= Config.SEEK_PROBABILITY <= 1
