"""
Unit tests for youtube_watcher module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from youtube_watcher import YouTubeWatcher
from proxy_manager import Proxy


class TestYouTubeWatcher:
    """Test YouTubeWatcher class"""

    def test_initialization(self):
        """Test YouTubeWatcher initialization"""
        watcher = YouTubeWatcher(browser_id=1, video_url='https://youtube.com/watch?v=test')

        assert watcher.browser_id == 1
        assert watcher.video_url == 'https://youtube.com/watch?v=test'
        assert watcher.browser is None
        assert watcher.context is None
        assert watcher.page is None
        assert watcher.proxy is None
        assert watcher.retry_count == 0
        assert watcher.strategy is not None
        assert 'name' in watcher.strategy

    # test_get_context_options_* removed as the method no longer exists in Selenium implementation

    def test_get_behavior_probability(self):
        """Test getting behavior probability"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.strategy = {
            'name': 'engaged_viewer',
            'probability_multiplier': 1.5
        }

        with patch('youtube_watcher.Config') as mock_config:
            mock_config.MOUSE_MOVEMENT_PROBABILITY = 0.4

            prob = watcher._get_behavior_probability('mouse_movement')

            # Should be base probability * multiplier, capped at 1.0
            expected = min(1.0, 0.4 * 1.5)
            assert prob == expected

    def test_get_behavior_probability_unknown(self):
        """Test getting probability for unknown behavior"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.strategy = {
            'name': 'casual_viewer',
            'probability_multiplier': 1.0
        }

        prob = watcher._get_behavior_probability('unknown_behavior')

        # Should return default probability * multiplier
        assert 0 <= prob <= 1.0

    @pytest.mark.asyncio
    async def test_get_video_duration_success(self):
        """Test getting video duration successfully"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.page = AsyncMock()
        watcher.page.evaluate = AsyncMock(return_value=120.5)

        duration = await watcher.get_video_duration()

        assert duration == 120.5
        watcher.page.evaluate.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_video_duration_failure(self):
        """Test getting video duration when it fails"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.page = AsyncMock()
        watcher.page.evaluate = AsyncMock(return_value=0)

        duration = await watcher.get_video_duration()

        # Should return default duration
        assert duration == 180.0

    @pytest.mark.asyncio
    async def test_get_video_duration_error(self):
        """Test getting video duration with error"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.page = AsyncMock()
        watcher.page.evaluate = AsyncMock(side_effect=Exception("Test error"))

        duration = await watcher.get_video_duration()

        # Should return default duration
        assert duration == 180.0

    @pytest.mark.asyncio
    async def test_ensure_video_playing_paused(self):
        """Test ensuring video is playing when paused"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.page = AsyncMock()
        watcher.page.evaluate = AsyncMock(return_value=True)  # is_paused
        watcher.page.click = AsyncMock()

        await watcher.ensure_video_playing()

        # Should click to play
        watcher.page.click.assert_called_once_with('video')

    @pytest.mark.asyncio
    async def test_ensure_video_playing_already_playing(self):
        """Test ensuring video is playing when already playing"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.page = AsyncMock()
        watcher.page.evaluate = AsyncMock(return_value=False)  # not paused
        watcher.page.click = AsyncMock()

        await watcher.ensure_video_playing()

        # Should not click
        watcher.page.click.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_popups(self):
        """Test handling popups"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.page = AsyncMock()

        mock_locator = AsyncMock()
        mock_locator.first = AsyncMock()
        mock_locator.first.is_visible = AsyncMock(return_value=True)
        mock_locator.first.click = AsyncMock()
        watcher.page.locator = Mock(return_value=mock_locator)

        await watcher.handle_popups()

        # Should attempt to find and click buttons
        assert watcher.page.locator.call_count > 0

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup method"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')
        watcher.page = AsyncMock()
        watcher.context = AsyncMock()
        watcher.browser = AsyncMock()

        await watcher.cleanup()

        # Should close all resources
        watcher.page.close.assert_called_once()
        watcher.context.close.assert_called_once()
        watcher.browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_with_none_values(self):
        """Test cleanup when resources are None"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        # Should not raise error
        await watcher.cleanup()

    def test_strategy_assigned(self):
        """Test that watching strategy is assigned"""
        watcher = YouTubeWatcher(0, 'https://youtube.com/watch?v=test')

        assert watcher.strategy is not None
        assert isinstance(watcher.strategy, dict)
        assert 'name' in watcher.strategy
        assert 'watch_percentage' in watcher.strategy
        assert 'interaction_frequency' in watcher.strategy
        assert 'probability_multiplier' in watcher.strategy
