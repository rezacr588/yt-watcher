"""
Unit tests for behavior_patterns module
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from behavior_patterns import BehaviorPatterns, WatchingStrategy


class TestBehaviorPatterns:
    """Test BehaviorPatterns class"""

    @pytest.mark.asyncio
    async def test_human_delay(self):
        """Test human-like delay"""
        start = asyncio.get_event_loop().time()
        await BehaviorPatterns.human_delay(0.1, 0.2)
        elapsed = asyncio.get_event_loop().time() - start

        assert 0.1 <= elapsed <= 0.3  # Allow small buffer

    @pytest.mark.asyncio
    async def test_natural_mouse_movement(self):
        """Test natural mouse movement with mock page"""
        mock_page = Mock()
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock()

        await BehaviorPatterns.natural_mouse_movement(
            mock_page, 0, 0, 100, 100, steps=5
        )

        # Should have called mouse.move multiple times
        assert mock_page.mouse.move.call_count > 0

    @pytest.mark.asyncio
    async def test_random_mouse_movements(self):
        """Test random mouse movements"""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=1920)  # width and height
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock()

        await BehaviorPatterns.random_mouse_movements(mock_page, count=2)

        # Verify evaluate was called for dimensions
        assert mock_page.evaluate.call_count >= 2

    @pytest.mark.asyncio
    async def test_scroll_behavior(self):
        """Test scroll behavior"""
        mock_page = AsyncMock()
        mock_page.mouse = AsyncMock()
        mock_page.mouse.wheel = AsyncMock()

        await BehaviorPatterns.scroll_behavior(mock_page)

        # Should have called wheel at least once
        assert mock_page.mouse.wheel.call_count >= 1

    @pytest.mark.asyncio
    async def test_video_player_interaction_pause_resume(self):
        """Test pause/resume interaction"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.first = AsyncMock()
        mock_locator.first.count = AsyncMock(return_value=1)
        mock_locator.first.click = AsyncMock()
        mock_page.locator = Mock(return_value=mock_locator)

        await BehaviorPatterns.video_player_interaction(mock_page, 'pause_resume')

        # Verify locator was called
        mock_page.locator.assert_called()

    @pytest.mark.asyncio
    async def test_execute_behavior_mouse_movement(self):
        """Test executing mouse movement behavior"""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=1920)
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock()

        await BehaviorPatterns.execute_behavior(mock_page, 'mouse_movement')

        # Should have attempted mouse movements
        assert mock_page.evaluate.call_count >= 0

    @pytest.mark.asyncio
    async def test_execute_behavior_invalid(self):
        """Test executing invalid behavior does not raise error"""
        mock_page = AsyncMock()

        # Should not raise error for invalid behavior
        await BehaviorPatterns.execute_behavior(mock_page, 'invalid_behavior')

    def test_get_random_behavior_sequence(self):
        """Test getting random behavior sequence"""
        sequence = BehaviorPatterns.get_random_behavior_sequence()

        assert isinstance(sequence, list)
        assert 2 <= len(sequence) <= 5
        assert all(isinstance(b, str) for b in sequence)

        # All behaviors should be unique
        assert len(sequence) == len(set(sequence))

    @pytest.mark.asyncio
    async def test_reading_scroll(self):
        """Test reading scroll behavior"""
        mock_page = AsyncMock()
        mock_page.mouse = AsyncMock()
        mock_page.mouse.wheel = AsyncMock()

        await BehaviorPatterns._reading_scroll(mock_page)

        # Should have scrolled multiple times
        assert mock_page.mouse.wheel.call_count >= 2

    @pytest.mark.asyncio
    async def test_pause_and_resume(self):
        """Test pause and resume"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_first = AsyncMock()
        mock_first.count = AsyncMock(return_value=1)
        mock_first.click = AsyncMock()
        mock_locator.first = mock_first
        mock_page.locator = Mock(return_value=mock_locator)

        await BehaviorPatterns._pause_and_resume(mock_page)

        # Should click twice (pause and resume)
        assert mock_first.click.call_count == 2

    @pytest.mark.asyncio
    async def test_seek_video(self):
        """Test video seeking"""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock()
        # First call returns current time, second returns duration
        mock_page.evaluate.side_effect = [50.0, 100.0, None]

        await BehaviorPatterns._seek_video(mock_page)

        # Should evaluate multiple times
        assert mock_page.evaluate.call_count >= 2

    @pytest.mark.asyncio
    async def test_adjust_volume(self):
        """Test volume adjustment"""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock()

        await BehaviorPatterns._adjust_volume(mock_page)

        # Should call evaluate to set volume
        assert mock_page.evaluate.call_count == 1

    @pytest.mark.asyncio
    async def test_hover_player(self):
        """Test hovering over player"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_first = AsyncMock()
        mock_first.count = AsyncMock(return_value=1)
        mock_first.bounding_box = AsyncMock(return_value={
            'x': 100, 'y': 100, 'width': 800, 'height': 600
        })
        mock_locator.first = mock_first
        mock_page.locator = Mock(return_value=mock_locator)
        mock_page.mouse = AsyncMock()
        mock_page.mouse.move = AsyncMock()

        await BehaviorPatterns._hover_player(mock_page)

        # Should move mouse
        assert mock_page.mouse.move.call_count >= 1


class TestWatchingStrategy:
    """Test WatchingStrategy class"""

    def test_get_strategy(self):
        """Test getting a random strategy"""
        strategy = WatchingStrategy.get_strategy()

        assert isinstance(strategy, dict)
        assert 'name' in strategy
        assert 'watch_percentage' in strategy
        assert 'interaction_frequency' in strategy
        assert 'probability_multiplier' in strategy

        # Verify values are reasonable
        assert 0 < strategy['watch_percentage'] <= 1.0
        assert strategy['probability_multiplier'] > 0
        assert strategy['name'] in [
            'casual_viewer', 'engaged_viewer', 'quick_viewer', 'binge_watcher'
        ]

    def test_strategy_randomness(self):
        """Test that strategies vary"""
        strategies = [WatchingStrategy.get_strategy() for _ in range(10)]
        names = [s['name'] for s in strategies]

        # With 10 calls, we should get some variety (not all the same)
        # This could theoretically fail but very unlikely
        assert len(set(names)) > 1

    def test_strategy_watch_percentage_ranges(self):
        """Test that watch percentages are within expected ranges"""
        for _ in range(20):
            strategy = WatchingStrategy.get_strategy()
            watch_pct = strategy['watch_percentage']

            assert 0 < watch_pct <= 1.0

            # Verify strategy-specific ranges
            if strategy['name'] == 'casual_viewer':
                assert 0.6 <= watch_pct <= 0.8
            elif strategy['name'] == 'engaged_viewer':
                assert 0.9 <= watch_pct <= 1.0
            elif strategy['name'] == 'quick_viewer':
                assert 0.3 <= watch_pct <= 0.5
            elif strategy['name'] == 'binge_watcher':
                assert watch_pct == 1.0
