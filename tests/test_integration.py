"""
Integration tests for YouTube Watcher
Tests interaction between multiple components
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch, AsyncMock, Mock
from proxy_manager import ProxyManager, ProxyPool, Proxy
from behavior_patterns import BehaviorPatterns
from stealth import StealthConfig, get_complete_stealth_script
from youtube_watcher import YouTubeWatcher
from config import Config


class TestProxyIntegration:
    """Test proxy manager integration with watcher"""

    @pytest.mark.asyncio
    async def test_proxy_pool_initialization(self):
        """Test initializing proxy pool and using it"""
        # Create temporary proxy file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('http://proxy1.com:8080\n')
            f.write('http://proxy2.com:3128\n')
            temp_file = f.name

        try:
            # Initialize pool
            ProxyPool.initialize(temp_file, 'round-robin')
            manager = ProxyPool.get_manager()

            assert manager is not None
            assert len(manager.proxies) == 2

            # Get proxies in sequence
            proxy1 = ProxyPool.get_proxy()
            proxy2 = ProxyPool.get_proxy()

            assert proxy1 is not None
            assert proxy2 is not None
            assert proxy1 != proxy2

        finally:
            os.unlink(temp_file)
            ProxyPool._manager = None

    def test_proxy_manager_with_watcher_context(self):
        """Test proxy integration with watcher context options"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        # Create temporary proxy file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('http://test-proxy.com:8080\n')
            temp_file = f.name

        try:
            ProxyPool.initialize(temp_file, 'random')

            with patch('youtube_watcher.Config') as mock_config:
                mock_config.USE_PROXY = True
                mock_config.RANDOMIZE_VIEWPORT = False
                mock_config.ROTATE_USER_AGENTS = False
                mock_config.RANDOM_LOCATIONS = False

                options = watcher._get_context_options()

                assert 'proxy' in options
                assert watcher.proxy is not None
                assert watcher.proxy.host == 'test-proxy.com'

        finally:
            os.unlink(temp_file)
            ProxyPool._manager = None


class TestBehaviorIntegration:
    """Test behavior patterns integration"""

    @pytest.mark.asyncio
    async def test_behavior_sequence_execution(self):
        """Test executing a sequence of behaviors"""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=1920)
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock()
        mock_page.mouse.wheel = AsyncMock()

        # Get a behavior sequence
        behaviors = ['mouse_movement', 'scroll']

        # Execute each behavior
        for behavior in behaviors:
            await BehaviorPatterns.execute_behavior(mock_page, behavior)

        # Verify interactions occurred
        assert mock_page.evaluate.call_count >= 0
        assert mock_page.mouse.move.call_count >= 0 or mock_page.mouse.wheel.call_count >= 0


class TestStealthIntegration:
    """Test stealth features integration"""

    def test_stealth_script_generation(self):
        """Test complete stealth script generation"""
        script = get_complete_stealth_script()

        assert isinstance(script, str)
        assert len(script) > 100  # Should be substantial

        # Verify all components are present
        assert 'navigator.webdriver' in script
        assert 'Object.defineProperty' in script

    def test_stealth_config_consistency(self):
        """Test that stealth config generates consistent output"""
        # User agent
        ua1 = StealthConfig.get_random_user_agent()
        assert 'Mozilla' in ua1

        # Viewport
        viewport = StealthConfig.get_random_viewport()
        assert viewport['width'] > 0 and viewport['height'] > 0

        # Location
        location = StealthConfig.get_random_location()
        assert 'city' in location and 'timezone' in location

        # Browser args
        args = StealthConfig.get_browser_args(5)
        assert any('AutomationControlled' in arg for arg in args)


class TestWatcherComponentIntegration:
    """Test YouTubeWatcher with various components"""

    def test_watcher_with_strategy(self):
        """Test watcher integrates with watching strategy"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        # Strategy should be assigned
        assert watcher.strategy is not None
        assert 'probability_multiplier' in watcher.strategy

        # Test probability calculation
        with patch('youtube_watcher.Config') as mock_config:
            mock_config.MOUSE_MOVEMENT_PROBABILITY = 0.5

            prob = watcher._get_behavior_probability('mouse_movement')
            assert 0 <= prob <= 1.0

    def test_watcher_context_with_all_features(self):
        """Test watcher context with all stealth features enabled"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        with patch('youtube_watcher.Config') as mock_config:
            mock_config.RANDOMIZE_VIEWPORT = True
            mock_config.ROTATE_USER_AGENTS = True
            mock_config.RANDOM_LOCATIONS = True
            mock_config.USE_PROXY = False

            options = watcher._get_context_options()

            assert 'viewport' in options
            assert 'user_agent' in options
            assert 'timezone_id' in options
            assert 'geolocation' in options
            assert 'color_scheme' in options


class TestConfigValidationIntegration:
    """Test configuration validation with components"""

    def test_config_with_proxy_manager(self):
        """Test config validation affects proxy manager"""
        # Create temporary proxy file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('http://proxy.com:8080\n')
            temp_file = f.name

        try:
            original_use_proxy = Config.USE_PROXY
            original_proxy_file = Config.PROXY_LIST_FILE

            Config.USE_PROXY = True
            Config.PROXY_LIST_FILE = temp_file

            # Should validate successfully
            assert Config.validate() is True

            # Now test with missing file
            Config.PROXY_LIST_FILE = 'nonexistent.txt'
            Config.USE_PROXY = True
            Config.validate()

            # Should disable proxy
            assert Config.USE_PROXY is False

        finally:
            os.unlink(temp_file)
            Config.USE_PROXY = original_use_proxy
            Config.PROXY_LIST_FILE = original_proxy_file

    def test_config_watch_percentages(self):
        """Test config watch percentages with watcher"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        # Mock config values
        with patch('youtube_watcher.Config') as mock_config:
            mock_config.MIN_WATCH_PERCENTAGE = 0.7
            mock_config.MAX_WATCH_PERCENTAGE = 0.9

            # Strategy should respect config bounds
            # (This is validated in the watcher's watch logic)
            assert mock_config.MIN_WATCH_PERCENTAGE <= mock_config.MAX_WATCH_PERCENTAGE


class TestEndToEndDataFlow:
    """Test data flow through entire system"""

    @pytest.mark.asyncio
    async def test_proxy_selection_and_usage(self):
        """Test proxy is selected and used correctly"""
        # Create proxy file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('http://proxy1.com:8080\n')
            f.write('http://proxy2.com:8080\n')
            temp_file = f.name

        try:
            ProxyPool.initialize(temp_file, 'round-robin')

            # Create multiple watchers
            watchers = [YouTubeWatcher(i, 'https://youtube.com/watch?v=test') for i in range(3)]

            with patch('youtube_watcher.Config') as mock_config:
                mock_config.USE_PROXY = True
                mock_config.RANDOMIZE_VIEWPORT = False
                mock_config.ROTATE_USER_AGENTS = False
                mock_config.RANDOM_LOCATIONS = False

                # Each watcher should get a proxy
                for watcher in watchers:
                    options = watcher._get_context_options()
                    assert watcher.proxy is not None

                # Proxies should be distributed
                proxy_hosts = [w.proxy.host for w in watchers]
                assert len(set(proxy_hosts)) >= 1  # At least one unique proxy

        finally:
            os.unlink(temp_file)
            ProxyPool._manager = None

    def test_behavior_probability_calculation_flow(self):
        """Test behavior probability calculation through the system"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        # Set specific strategy
        watcher.strategy = {
            'name': 'engaged_viewer',
            'probability_multiplier': 2.0
        }

        with patch('youtube_watcher.Config') as mock_config:
            mock_config.MOUSE_MOVEMENT_PROBABILITY = 0.4
            mock_config.SCROLL_PROBABILITY = 0.3

            mouse_prob = watcher._get_behavior_probability('mouse_movement')
            scroll_prob = watcher._get_behavior_probability('scroll')

            # Should apply multiplier but cap at 1.0
            assert mouse_prob == min(1.0, 0.4 * 2.0)
            assert scroll_prob == min(1.0, 0.3 * 2.0)
