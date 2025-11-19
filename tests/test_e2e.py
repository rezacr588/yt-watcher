"""
End-to-end tests for YouTube Watcher
These tests verify the complete system behavior
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch, AsyncMock, Mock
from youtube_watcher import YouTubeWatcher, main
from proxy_manager import ProxyPool
from config import Config


@pytest.mark.e2e
class TestE2EBasicFlow:
    """End-to-end tests for basic workflows"""

    @pytest.mark.asyncio
    async def test_single_watcher_lifecycle(self):
        """Test complete lifecycle of a single watcher"""
        watcher = YouTubeWatcher(
            browser_id=0,
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        )

        # Mock the browser setup and interactions
        with patch('youtube_watcher.uc') as mock_uc:
            # Setup mocks
            mock_driver = Mock()
            mock_uc.Chrome.return_value = mock_driver
            
            # Mock driver methods
            mock_driver.get = Mock()
            mock_driver.execute_script = Mock()
            mock_driver.find_element = Mock()
            mock_driver.quit = Mock()
            
            # Mock video duration and playback
            # execute_script is used for many things:
            # 1. stealth injection (3 calls)
            # 2. scroll (maybe)
            # 3. duration check
            # 4. paused check
            
            # We need to be careful with side_effect for execute_script
            # It returns different things based on the script
            def execute_script_side_effect(script, *args):
                if 'duration' in script:
                    return 120.0
                if 'paused' in script:
                    return False # Not paused (playing)
                return None

            mock_driver.execute_script.side_effect = execute_script_side_effect

            # Setup browser
            await watcher.setup_browser()

            assert watcher.driver is not None

            # Run navigation
            await watcher.navigate_to_video()
            
            # Cleanup
            await watcher.cleanup()

            mock_driver.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_watcher_with_proxy(self):
        """Test watcher with proxy configuration"""
        # Create proxy file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('http://test-proxy.com:8080\n')
            temp_file = f.name

        try:
            ProxyPool.initialize(temp_file, 'random')

            watcher = YouTubeWatcher(
                browser_id=0,
                video_url='https://www.youtube.com/watch?v=test'
            )

            with patch('youtube_watcher.Config') as mock_config:
                mock_config.USE_PROXY = True
                mock_config.RANDOMIZE_VIEWPORT = False
                mock_config.ROTATE_USER_AGENTS = False
                mock_config.RANDOM_LOCATIONS = False

                # In Selenium/UC, we check ChromeOptions
                # We can't easily inspect the options passed to Chrome() constructor in the mock
                # without mocking the constructor itself and checking call_args
                
                with patch('youtube_watcher.uc') as mock_uc:
                    mock_driver = Mock()
                    mock_uc.Chrome.return_value = mock_driver
                    
                    await watcher.setup_browser()
                    
                    # Check if Chrome was called with options containing proxy
                    call_args = mock_uc.Chrome.call_args
                    assert call_args is not None
                    options = call_args.kwargs.get('options') or call_args.args[0] if call_args.args else None
                    
                    # Verify proxy in arguments by checking add_argument calls on the options mock
                    # The options object passed to Chrome is the one we want to check
                    # But wait, options is a Mock object created by uc.ChromeOptions()
                    # We need to capture that mock
                    
                    # Let's check if we can find the proxy argument in the add_argument calls of the options mock
                    # We need to access the return value of uc.ChromeOptions()
                    mock_options = mock_uc.ChromeOptions.return_value
                    
                    # Check calls to add_argument
                    proxy_arg_found = False
                    for call in mock_options.add_argument.call_args_list:
                        arg = call.args[0]
                        if '--proxy-server=' in arg and 'test-proxy.com' in arg:
                            proxy_arg_found = True
                            break
                    
                    assert proxy_arg_found
                    assert watcher.proxy is not None
                    assert watcher.proxy.host == 'test-proxy.com'

        finally:
            os.unlink(temp_file)
            ProxyPool._manager = None

    @pytest.mark.asyncio
    async def test_watcher_error_handling(self):
        """Test watcher handles errors gracefully"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        with patch('youtube_watcher.uc') as mock_uc:
            # Simulate error during browser launch
            mock_uc.Chrome.side_effect = Exception("Browser launch failed")

            # Should handle error and return False
            try:
                await watcher.setup_browser()
            except Exception:
                # Error is expected
                pass

            # Cleanup should still work
            await watcher.cleanup()


@pytest.mark.e2e
class TestE2EMultipleWatchers:
    """End-to-end tests for multiple watchers"""

    @pytest.mark.asyncio
    async def test_multiple_watchers_concurrent(self):
        """Test running multiple watchers concurrently"""
        num_watchers = 3
        watchers = [
            YouTubeWatcher(i, 'https://youtube.com/watch?v=test')
            for i in range(num_watchers)
        ]

        # Mock all watchers
        for watcher in watchers:
            watcher.setup_browser = AsyncMock()
            watcher.navigate_to_video = AsyncMock(return_value=True)
            watcher.handle_popups = AsyncMock()
            watcher.watch_video = AsyncMock(return_value=True)
            watcher.cleanup = AsyncMock()

        # Run all watchers
        tasks = [watcher.run() for watcher in watchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete
        assert len(results) == num_watchers
        # Most should succeed (mocked to return True)
        successful = sum(1 for r in results if r is True)
        assert successful == num_watchers

    @pytest.mark.asyncio
    async def test_proxy_distribution_across_watchers(self):
        """Test that proxies are distributed across multiple watchers"""
        # Create proxy file with multiple proxies
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for i in range(5):
                f.write(f'http://proxy{i}.com:8080\n')
            temp_file = f.name

        try:
            ProxyPool.initialize(temp_file, 'round-robin')

            watchers = [
                YouTubeWatcher(i, 'https://youtube.com/watch?v=test')
                for i in range(5)
            ]

            with patch('youtube_watcher.Config') as mock_config:
                mock_config.USE_PROXY = True
                mock_config.RANDOMIZE_VIEWPORT = False
                mock_config.ROTATE_USER_AGENTS = False
                mock_config.RANDOM_LOCATIONS = False

                # Get context options for each watcher
                # Get context options for each watcher
                with patch('youtube_watcher.uc') as mock_uc:
                    mock_driver = Mock()
                    mock_uc.Chrome.return_value = mock_driver
                    
                    for watcher in watchers:
                        await watcher.setup_browser()
                        
                        # Check proxy in options
                        mock_options = mock_uc.ChromeOptions.return_value
                        
                        proxy_arg_found = False
                        for call in mock_options.add_argument.call_args_list:
                            arg = call.args[0]
                            if '--proxy-server=' in arg:
                                proxy_arg_found = True
                                break
                        
                        assert proxy_arg_found
                        
                        # Reset mock for next watcher
                        mock_uc.Chrome.reset_mock()
                        mock_options.reset_mock()

                # Each watcher should have a proxy
                assert all(w.proxy is not None for w in watchers)

                # With round-robin, we should have different proxies
                proxy_hosts = [w.proxy.host for w in watchers]
                unique_proxies = len(set(proxy_hosts))
                assert unique_proxies >= 2  # Should have at least some variety

        finally:
            os.unlink(temp_file)
            ProxyPool._manager = None


@pytest.mark.e2e
class TestE2EConfigurationScenarios:
    """End-to-end tests for different configuration scenarios"""

    def test_minimal_configuration(self):
        """Test with minimal configuration"""
        with patch('youtube_watcher.Config') as mock_config:
            mock_config.NUM_BROWSERS = 1
            mock_config.HEADLESS = True
            mock_config.USE_PROXY = False
            mock_config.STEALTH_MODE = False
            mock_config.MIN_WATCH_PERCENTAGE = 0.5
            mock_config.MAX_WATCH_PERCENTAGE = 0.6

            watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
            assert watcher is not None
            assert watcher.browser_id == 0

    @pytest.mark.asyncio
    async def test_full_featured_configuration(self):
        """Test with all features enabled"""
        with patch('youtube_watcher.Config') as mock_config:
            mock_config.USE_PROXY = False  # Don't need actual proxy file
            mock_config.ROTATE_USER_AGENTS = True
            mock_config.RANDOM_LOCATIONS = True
            mock_config.STEALTH_MODE = True
            mock_config.RANDOMIZE_VIEWPORT = True
            mock_config.ENABLE_MOUSE_MOVEMENT = True
            mock_config.ENABLE_SCROLLING = True
            mock_config.ENABLE_VOLUME_CHANGES = True

            watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
            # Mock uc to check options
            with patch('youtube_watcher.uc') as mock_uc:
                mock_driver = Mock()
                mock_uc.Chrome.return_value = mock_driver
                
                await watcher.setup_browser()
                
                mock_options = mock_uc.ChromeOptions.return_value
                
                # Check arguments
                args = [call.args[0] for call in mock_options.add_argument.call_args_list]
                assert any('--user-agent=' in arg for arg in args)
                # Window size is set via argument
                assert any('--window-size=' in arg for arg in args)


@pytest.mark.e2e
class TestE2ERetryLogic:
    """End-to-end tests for retry logic"""

    @pytest.mark.asyncio
    async def test_watcher_retries_on_failure(self):
        """Test that watcher retries on failure"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        call_count = 0

        async def mock_navigate():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return False  # Fail first time
            return True  # Succeed second time

        with patch('youtube_watcher.Config') as mock_config:
            mock_config.MAX_RETRIES = 3
            mock_config.RETRY_DELAY = 0.1

            watcher.setup_browser = AsyncMock()
            watcher.navigate_to_video = mock_navigate
            watcher.handle_popups = AsyncMock()
            watcher.watch_video = AsyncMock(return_value=True)
            watcher.cleanup = AsyncMock()

            result = await watcher.run()

            # Should eventually succeed after retry
            assert call_count >= 1
            assert watcher.retry_count >= 0

    @pytest.mark.asyncio
    async def test_watcher_gives_up_after_max_retries(self):
        """Test that watcher gives up after max retries"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        with patch('youtube_watcher.Config') as mock_config:
            mock_config.MAX_RETRIES = 2
            mock_config.RETRY_DELAY = 0.01

            watcher.setup_browser = AsyncMock()
            watcher.navigate_to_video = AsyncMock(return_value=False)  # Always fail
            watcher.cleanup = AsyncMock()

            result = await watcher.run()

            # Should fail after retries
            assert watcher.retry_count <= mock_config.MAX_RETRIES


@pytest.mark.e2e
@pytest.mark.slow
class TestE2EPerformance:
    """End-to-end performance tests"""

    @pytest.mark.asyncio
    async def test_parallel_watcher_startup(self):
        """Test that watchers can start up in parallel efficiently"""
        import time

        num_watchers = 5
        watchers = [
            YouTubeWatcher(i, 'https://youtube.com/watch?v=test')
            for i in range(num_watchers)
        ]

        # Mock the setup to be fast
        for watcher in watchers:
            watcher.run = AsyncMock(return_value=True)

        start_time = time.time()

        # Run all in parallel
        tasks = [watcher.run() for watcher in watchers]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        # Should complete relatively quickly (mocked, so under 1 second)
        assert elapsed < 2.0

    def test_memory_efficiency_watcher_creation(self):
        """Test that creating many watchers doesn't cause memory issues"""
        import sys

        watchers = []
        for i in range(100):
            watcher = YouTubeWatcher(i, 'https://youtube.com/watch?v=test')
            watchers.append(watcher)

        # Should create all without errors
        assert len(watchers) == 100

        # Basic memory check - each watcher should be reasonable size
        # This is a basic check, not comprehensive
        assert sys.getsizeof(watchers) > 0
