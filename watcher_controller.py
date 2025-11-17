"""
Controller for managing YouTube watchers from UI
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging

from youtube_watcher import YouTubeWatcher
from proxy_manager import ProxyPool
from config import Config

logger = logging.getLogger(__name__)


class WatcherController:
    """Manages watcher instances and their lifecycle"""

    def __init__(self):
        self.watchers: Dict[int, YouTubeWatcher] = {}
        self.tasks: Dict[int, asyncio.Task] = {}
        self.status: Dict[int, dict] = {}
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.total_successful = 0
        self.total_failed = 0

    async def start_watchers(self, config: dict, callback=None):
        """
        Start watchers with given configuration

        Args:
            config: Dictionary with settings
            callback: Optional callback for status updates
        """
        if self.is_running:
            logger.warning("Watchers already running")
            return {"error": "Watchers already running"}

        try:
            # Update configuration
            self._update_config(config)

            # Validate configuration
            Config.validate()

            # Initialize proxy pool if needed
            if Config.USE_PROXY:
                ProxyPool.initialize(Config.PROXY_LIST_FILE, Config.PROXY_ROTATION)
                manager = ProxyPool.get_manager()
                if manager and manager.proxies:
                    logger.info("Testing proxies...")
                    if callback:
                        callback('status', {'message': 'Testing proxies...', 'type': 'info'})
                    working = await manager.test_all_proxies(concurrent=10)
                    if working == 0:
                        logger.warning("No working proxies found! Disabling proxies...")
                        Config.USE_PROXY = False
                    else:
                        logger.info(f"Proxy test complete: {working} working proxies")
                        if callback:
                            callback('status', {'message': f'{working} proxies ready', 'type': 'success'})

            # Create watcher instances
            self.watchers.clear()
            self.tasks.clear()
            self.status.clear()
            self.total_successful = 0
            self.total_failed = 0
            self.is_running = True
            self.start_time = datetime.now()

            num_browsers = Config.NUM_BROWSERS
            video_url = Config.VIDEO_URL

            logger.info(f"Starting {num_browsers} watchers for {video_url}")
            if callback:
                callback('status', {'message': f'Launching {num_browsers} watchers...', 'type': 'info'})

            # Launch watchers with staggered delays
            for i in range(num_browsers):
                watcher = YouTubeWatcher(i, video_url)
                self.watchers[i] = watcher
                self.status[i] = {
                    'id': i,
                    'status': 'initializing',
                    'progress': 0,
                    'message': 'Starting...',
                    'strategy': watcher.strategy['name'],
                    'proxy': None,
                    'start_time': datetime.now().isoformat()
                }

                # Stagger launches
                if i > 0:
                    delay = asyncio.create_task(
                        asyncio.sleep(Config.LAUNCH_DELAY_MIN + (Config.LAUNCH_DELAY_MAX - Config.LAUNCH_DELAY_MIN) * (i / num_browsers))
                    )
                    await delay

                # Create task with callback wrapper
                task = asyncio.create_task(
                    self._run_watcher_with_updates(i, watcher, callback)
                )
                self.tasks[i] = task

                logger.info(f"Launched watcher {i}")
                if callback:
                    callback('watcher_update', self.status[i])

            # Wait for all to complete
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)

            self.is_running = False
            logger.info(f"All watchers completed. Success: {self.total_successful}, Failed: {self.total_failed}")

            if callback:
                callback('status', {
                    'message': f'Completed! Success: {self.total_successful}/{num_browsers}',
                    'type': 'success'
                })

            return {
                'success': True,
                'total': num_browsers,
                'successful': self.total_successful,
                'failed': self.total_failed
            }

        except Exception as e:
            self.is_running = False
            logger.error(f"Error starting watchers: {e}", exc_info=True)
            if callback:
                callback('status', {'message': f'Error: {str(e)}', 'type': 'error'})
            return {"error": str(e)}

    async def _run_watcher_with_updates(self, watcher_id: int, watcher: YouTubeWatcher, callback):
        """Run watcher and emit status updates"""
        try:
            # Setup phase
            self.status[watcher_id]['status'] = 'running'
            self.status[watcher_id]['message'] = 'Setting up browser...'
            if callback:
                callback('watcher_update', self.status[watcher_id])
                callback('status_update', self.get_status())

            # Create a progress callback for the watcher
            async def progress_callback(message: str, progress: int = None):
                self.status[watcher_id]['message'] = message
                if progress is not None:
                    self.status[watcher_id]['progress'] = progress
                if callback:
                    callback('watcher_update', self.status[watcher_id])
                    callback('status_update', self.get_status())

            # Inject progress callback into watcher
            watcher.progress_callback = progress_callback

            # Run the watcher
            result = await watcher.run()

            # Update final status
            if result:
                self.total_successful += 1
                self.status[watcher_id]['status'] = 'completed'
                self.status[watcher_id]['message'] = 'Successfully completed'
                self.status[watcher_id]['progress'] = 100
            else:
                self.total_failed += 1
                self.status[watcher_id]['status'] = 'failed'
                self.status[watcher_id]['message'] = 'Failed to complete'

            if callback:
                callback('watcher_update', self.status[watcher_id])
                callback('status_update', self.get_status())

            return result

        except Exception as e:
            self.total_failed += 1
            self.status[watcher_id]['status'] = 'error'
            self.status[watcher_id]['message'] = f'Error: {str(e)}'
            if callback:
                callback('watcher_update', self.status[watcher_id])
                callback('status_update', self.get_status())
            logger.error(f"Watcher {watcher_id} error: {e}", exc_info=True)
            return False

    def _update_config(self, config: dict):
        """Update Config with new values"""
        if 'video_url' in config:
            Config.VIDEO_URL = config['video_url']
        if 'num_browsers' in config:
            Config.NUM_BROWSERS = int(config['num_browsers'])
        if 'headless' in config:
            Config.HEADLESS = config['headless']
        if 'min_watch_percentage' in config:
            Config.MIN_WATCH_PERCENTAGE = float(config['min_watch_percentage'])
        if 'max_watch_percentage' in config:
            Config.MAX_WATCH_PERCENTAGE = float(config['max_watch_percentage'])
        if 'use_proxy' in config:
            Config.USE_PROXY = config['use_proxy']
        if 'proxy_rotation' in config:
            Config.PROXY_ROTATION = config['proxy_rotation']

    async def stop_watchers_async(self):
        """Stop all running watchers with proper cleanup"""
        if not self.is_running:
            return {"error": "No watchers running"}

        logger.info("Stopping all watchers...")
        for task_id, task in self.tasks.items():
            if not task.done():
                task.cancel()
                self.status[task_id]['status'] = 'cancelled'
                self.status[task_id]['message'] = 'Cancelled by user'

        # Wait for all tasks to complete cancellation
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)

        self.is_running = False
        return {"success": True, "message": "All watchers stopped"}

    def stop_watchers(self):
        """Stop all running watchers (sync wrapper)"""
        if not self.is_running:
            return {"error": "No watchers running"}

        logger.info("Stopping all watchers...")
        for task_id, task in self.tasks.items():
            if not task.done():
                task.cancel()
                self.status[task_id]['status'] = 'cancelled'
                self.status[task_id]['message'] = 'Cancelled by user'

        self.is_running = False
        return {"success": True, "message": "All watchers stopping..."}

    def get_status(self) -> dict:
        """Get current status of all watchers"""
        elapsed = None
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()

        return {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'elapsed_seconds': elapsed,
            'total_watchers': len(self.watchers),
            'successful': self.total_successful,
            'failed': self.total_failed,
            'watchers': list(self.status.values())
        }

    def get_config(self) -> dict:
        """Get current configuration"""
        return {
            'video_url': Config.VIDEO_URL,
            'num_browsers': Config.NUM_BROWSERS,
            'headless': Config.HEADLESS,
            'min_watch_percentage': Config.MIN_WATCH_PERCENTAGE,
            'max_watch_percentage': Config.MAX_WATCH_PERCENTAGE,
            'use_proxy': Config.USE_PROXY,
            'proxy_rotation': Config.PROXY_ROTATION,
            'proxy_file': Config.PROXY_LIST_FILE
        }
