"""
Tests for watcher_controller module
"""
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from watcher_controller import WatcherController
from config import Config


class TestWatcherController:
    """Test WatcherController class"""

    @pytest.fixture
    def controller(self):
        """Create controller instance"""
        return WatcherController()

    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        return {
            'video_url': 'https://www.youtube.com/watch?v=test',
            'num_browsers': 2,
            'headless': True,
            'min_watch_percentage': 0.5,
            'max_watch_percentage': 0.8,
            'use_proxy': False,
            'proxy_rotation': 'random'
        }

    def test_initialization(self, controller):
        """Test controller initialization"""
        assert controller.watchers == {}
        assert controller.tasks == {}
        assert controller.status == {}
        assert controller.is_running is False
        assert controller.start_time is None
        assert controller.total_successful == 0
        assert controller.total_failed == 0
        assert controller.continuous_mode is True
        assert controller.iteration_counts == {}

    def test_update_config(self, controller, mock_config):
        """Test configuration update"""
        controller._update_config(mock_config)

        assert Config.VIDEO_URL == mock_config['video_url']
        assert Config.NUM_BROWSERS == mock_config['num_browsers']
        assert Config.HEADLESS == mock_config['headless']
        assert Config.MIN_WATCH_PERCENTAGE == mock_config['min_watch_percentage']
        assert Config.MAX_WATCH_PERCENTAGE == mock_config['max_watch_percentage']
        assert Config.USE_PROXY == mock_config['use_proxy']
        assert Config.PROXY_ROTATION == mock_config['proxy_rotation']

    def test_get_config(self, controller):
        """Test get_config method"""
        config = controller.get_config()

        assert 'video_url' in config
        assert 'num_browsers' in config
        assert 'headless' in config
        assert 'min_watch_percentage' in config
        assert 'max_watch_percentage' in config
        assert 'use_proxy' in config
        assert 'proxy_rotation' in config
        assert 'proxy_file' in config

    def test_get_status_no_watchers(self, controller):
        """Test get_status with no watchers"""
        status = controller.get_status()

        assert status['is_running'] is False
        assert status['start_time'] is None
        assert status['elapsed_seconds'] is None
        assert status['total_watchers'] == 0
        assert status['successful'] == 0
        assert status['failed'] == 0
        assert status['watchers'] == []

    def test_get_status_with_watchers(self, controller):
        """Test get_status with running watchers"""
        controller.is_running = True
        controller.start_time = datetime.now()
        controller.total_successful = 5
        controller.total_failed = 2
        controller.status = {
            0: {'id': 0, 'status': 'running'},
            1: {'id': 1, 'status': 'completed'}
        }

        status = controller.get_status()

        assert status['is_running'] is True
        assert status['start_time'] is not None
        assert status['elapsed_seconds'] is not None
        assert status['total_watchers'] == 0  # No watchers in dict yet
        assert status['successful'] == 5
        assert status['failed'] == 2
        assert len(status['watchers']) == 2

    @pytest.mark.asyncio
    async def test_start_watchers_already_running(self, controller, mock_config):
        """Test start_watchers when already running"""
        controller.is_running = True

        result = await controller.start_watchers(mock_config)

        assert 'error' in result
        assert result['error'] == 'Watchers already running'

    @pytest.mark.asyncio
    async def test_start_watchers_validation_error(self, controller):
        """Test start_watchers with invalid config"""
        bad_config = {
            'video_url': 'https://www.youtube.com/watch?v=test',
            'num_browsers': -1,  # Invalid
            'headless': True,
            'use_proxy': False
        }

        result = await controller.start_watchers(bad_config)

        assert 'error' in result
        assert controller.is_running is False

    @pytest.mark.asyncio
    async def test_start_watchers_success(self, controller, mock_config):
        """Test successful watcher start"""
        mock_callback = Mock()

        with patch('watcher_controller.YouTubeWatcher') as MockWatcher:
            mock_watcher = AsyncMock()
            mock_watcher.run = AsyncMock(return_value=True)
            mock_watcher.strategy = {'name': 'casual'}
            MockWatcher.return_value = mock_watcher

            # Create task to start watchers but cancel quickly
            task = asyncio.create_task(controller.start_watchers(mock_config, mock_callback))
            await asyncio.sleep(0.5)

            # Stop immediately
            controller.is_running = False

            try:
                await asyncio.wait_for(task, timeout=2.0)
            except asyncio.TimeoutError:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_run_watcher_with_updates_success(self, controller):
        """Test _run_watcher_with_updates successful iteration"""
        mock_callback = Mock()
        mock_watcher = AsyncMock()
        mock_watcher.run = AsyncMock(return_value=True)

        controller.is_running = True
        controller.continuous_mode = True
        controller.status[0] = {
            'id': 0,
            'status': 'initializing',
            'progress': 0,
            'message': 'Starting...',
            'total_runs': 0
        }

        # Run one iteration then stop
        async def run_and_stop():
            await asyncio.sleep(0.1)
            controller.is_running = False

        stop_task = asyncio.create_task(run_and_stop())
        result = await controller._run_watcher_with_updates(0, mock_watcher, mock_callback)
        await stop_task

        assert result is True
        assert controller.status[0]['status'] == 'stopped'
        assert mock_callback.called

    @pytest.mark.asyncio
    async def test_run_watcher_with_updates_failure(self, controller):
        """Test _run_watcher_with_updates with watcher failure"""
        mock_callback = Mock()
        mock_watcher = AsyncMock()
        mock_watcher.run = AsyncMock(return_value=False)  # Watcher fails

        controller.is_running = True
        controller.continuous_mode = True
        controller.status[0] = {
            'id': 0,
            'status': 'initializing',
            'progress': 0,
            'message': 'Starting...',
            'total_runs': 0
        }

        # Run one iteration then stop
        async def run_and_stop():
            await asyncio.sleep(0.1)
            controller.is_running = False

        stop_task = asyncio.create_task(run_and_stop())
        result = await controller._run_watcher_with_updates(0, mock_watcher, mock_callback)
        await stop_task

        assert result is True  # Method completes successfully
        assert controller.total_failed > 0

    @pytest.mark.asyncio
    async def test_run_watcher_with_updates_cancelled(self, controller):
        """Test _run_watcher_with_updates cancellation"""
        mock_callback = Mock()
        mock_watcher = AsyncMock()
        mock_watcher.run = AsyncMock(side_effect=asyncio.CancelledError())

        controller.is_running = True
        controller.continuous_mode = True
        controller.status[0] = {
            'id': 0,
            'status': 'initializing',
            'progress': 0,
            'message': 'Starting...',
            'total_runs': 0
        }

        result = await controller._run_watcher_with_updates(0, mock_watcher, mock_callback)

        assert result is False
        assert controller.status[0]['status'] == 'cancelled'

    @pytest.mark.asyncio
    async def test_run_watcher_with_updates_exception(self, controller):
        """Test _run_watcher_with_updates with exception"""
        mock_callback = Mock()
        mock_watcher = AsyncMock()
        mock_watcher.run = AsyncMock(side_effect=RuntimeError("Test error"))

        controller.is_running = True
        controller.continuous_mode = True
        controller.status[0] = {
            'id': 0,
            'status': 'initializing',
            'progress': 0,
            'message': 'Starting...',
            'total_runs': 0
        }

        result = await controller._run_watcher_with_updates(0, mock_watcher, mock_callback)

        assert result is False
        assert controller.status[0]['status'] == 'error'
        assert 'Test error' in controller.status[0]['message']

    def test_stop_watchers_not_running(self, controller):
        """Test stop_watchers when not running"""
        result = controller.stop_watchers()

        assert 'error' in result
        assert result['error'] == 'No watchers running'

    def test_stop_watchers_running(self, controller):
        """Test stop_watchers when running"""
        controller.is_running = True
        mock_task = MagicMock()
        mock_task.done.return_value = False
        controller.tasks[0] = mock_task
        controller.status[0] = {'status': 'running'}

        result = controller.stop_watchers()

        assert result['success'] is True
        assert controller.is_running is False
        assert mock_task.cancel.called
        assert controller.status[0]['status'] == 'cancelled'

    @pytest.mark.asyncio
    async def test_stop_watchers_async_not_running(self, controller):
        """Test stop_watchers_async when not running"""
        result = await controller.stop_watchers_async()

        assert 'error' in result
        assert result['error'] == 'No watchers running'

    @pytest.mark.asyncio
    async def test_stop_watchers_async_running(self, controller):
        """Test stop_watchers_async when running"""
        controller.is_running = True

        # Create mock task
        mock_task = AsyncMock()
        mock_task.done.return_value = False
        mock_task.cancel = Mock()
        controller.tasks[0] = mock_task
        controller.status[0] = {'status': 'running'}

        result = await controller.stop_watchers_async()

        assert result['success'] is True
        assert controller.is_running is False

    @pytest.mark.asyncio
    async def test_progress_callback(self, controller):
        """Test progress callback functionality"""
        mock_callback = Mock()
        mock_watcher = AsyncMock()
        mock_watcher.run = AsyncMock(return_value=True)

        controller.is_running = True
        controller.continuous_mode = True
        controller.status[0] = {
            'id': 0,
            'status': 'initializing',
            'progress': 0,
            'message': 'Starting...',
            'total_runs': 0
        }

        # Run briefly then stop
        async def run_and_stop():
            await asyncio.sleep(0.1)
            controller.is_running = False

        stop_task = asyncio.create_task(run_and_stop())
        await controller._run_watcher_with_updates(0, mock_watcher, mock_callback)
        await stop_task

        # Verify callback was called
        assert mock_callback.called

    def test_iteration_tracking(self, controller):
        """Test iteration count tracking"""
        controller.iteration_counts[0] = 5
        controller.iteration_counts[1] = 3

        assert controller.iteration_counts[0] == 5
        assert controller.iteration_counts[1] == 3

    @pytest.mark.asyncio
    async def test_start_watchers_with_proxy(self, controller):
        """Test start_watchers with proxy configuration"""
        config = {
            'video_url': 'https://www.youtube.com/watch?v=test',
            'num_browsers': 1,
            'headless': True,
            'use_proxy': True,
            'proxy_rotation': 'random'
        }

        # Mock proxy pool
        with patch('watcher_controller.ProxyPool') as MockProxyPool:
            mock_manager = MagicMock()
            mock_manager.proxies = ['proxy1']
            mock_manager.test_all_proxies = AsyncMock(return_value=1)
            MockProxyPool.get_manager.return_value = mock_manager
            MockProxyPool.initialize = Mock()

            with patch('watcher_controller.YouTubeWatcher') as MockWatcher:
                mock_watcher = AsyncMock()
                mock_watcher.run = AsyncMock(return_value=True)
                mock_watcher.strategy = {'name': 'casual'}
                MockWatcher.return_value = mock_watcher

                # Start and stop quickly
                task = asyncio.create_task(controller.start_watchers(config))
                await asyncio.sleep(0.5)
                controller.is_running = False

                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except asyncio.TimeoutError:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
