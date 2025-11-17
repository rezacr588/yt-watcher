"""
YouTube Video Watcher with Advanced Anti-Detection
WARNING: This tool is for educational purposes only.
Using it to artificially inflate views violates YouTube's Terms of Service.
"""
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import random
import logging
from typing import Optional
import sys

from config import Config
from proxy_manager import ProxyPool, Proxy
from behavior_patterns import BehaviorPatterns, WatchingStrategy
from stealth import StealthConfig, get_complete_stealth_script

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class YouTubeWatcher:
    """Main class for watching YouTube videos with human-like behavior"""

    def __init__(self, browser_id: int, video_url: str):
        self.browser_id = browser_id
        self.video_url = video_url
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.proxy: Optional[Proxy] = None
        self.strategy = WatchingStrategy.get_strategy()
        self.retry_count = 0
        self.progress_callback = None  # For UI progress updates

    async def setup_browser(self):
        """Setup browser with stealth configuration"""
        self.playwright = await async_playwright().start()

        # Get browser arguments
        browser_args = StealthConfig.get_browser_args(self.browser_id)

        # Launch browser
        self.browser = await self.playwright.chromium.launch(
            headless=Config.HEADLESS,
            args=browser_args
        )

        # Setup context options
        context_options = self._get_context_options()

        # Create context
        self.context = await self.browser.new_context(**context_options)

        # Inject stealth scripts
        if Config.STEALTH_MODE:
            await self.context.add_init_script(get_complete_stealth_script())

        # Create page
        self.page = await self.context.new_page()

        logger.info(f"Browser {self.browser_id}: Setup complete with strategy '{self.strategy['name']}'")

    def _get_context_options(self) -> dict:
        """Get browser context options with randomization"""
        options = {}

        # Viewport
        if Config.RANDOMIZE_VIEWPORT:
            options['viewport'] = StealthConfig.get_random_viewport()
        else:
            options['viewport'] = {'width': 1920, 'height': 1080}

        # User agent
        if Config.ROTATE_USER_AGENTS:
            options['user_agent'] = StealthConfig.get_random_user_agent()
        else:
            options['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

        # Locale
        locale_settings = StealthConfig.get_locale_settings()
        options['locale'] = locale_settings['locale']

        # Location
        if Config.RANDOM_LOCATIONS:
            location = StealthConfig.get_random_location()
            options['timezone_id'] = location['timezone']
            options['geolocation'] = {
                'longitude': location['longitude'],
                'latitude': location['latitude']
            }
            options['permissions'] = ['geolocation']
        else:
            options['timezone_id'] = 'America/New_York'

        # Color scheme
        options['color_scheme'] = StealthConfig.get_color_scheme()

        # Proxy
        if Config.USE_PROXY:
            self.proxy = ProxyPool.get_proxy()
            if self.proxy:
                options['proxy'] = self.proxy.to_playwright_dict()
                logger.info(f"Browser {self.browser_id}: Using proxy {self.proxy.host}:{self.proxy.port}")
            else:
                logger.warning(f"Browser {self.browser_id}: No proxy available")

        return options

    async def navigate_to_video(self):
        """Navigate to YouTube video with natural browsing pattern"""
        try:
            # First visit YouTube homepage (more natural)
            logger.info(f"Browser {self.browser_id}: Visiting YouTube homepage")
            if self.progress_callback:
                await self.progress_callback("Visiting YouTube homepage...", 10)

            await self.page.goto('https://www.youtube.com', wait_until='domcontentloaded', timeout=30000)
            await BehaviorPatterns.human_delay(2, 4)

            # Perform some random actions on homepage
            if random.random() < 0.5:
                await BehaviorPatterns.random_mouse_movements(self.page, count=2)

            # Now navigate to the target video
            logger.info(f"Browser {self.browser_id}: Navigating to video")
            if self.progress_callback:
                await self.progress_callback("Navigating to video...", 20)

            await self.page.goto(self.video_url, wait_until='domcontentloaded', timeout=30000)

            # Wait for page to fully load
            await BehaviorPatterns.human_delay(3, 5)

            if self.progress_callback:
                await self.progress_callback("Video page loaded", 30)

            return True
        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Navigation error: {e}")
            return False

    async def handle_popups(self):
        """Handle cookie consent and other popups"""
        try:
            # Cookie consent
            cookie_selectors = [
                'button[aria-label*="Accept"]',
                'button[aria-label*="accept"]',
                'button:has-text("Accept all")',
                'button:has-text("I agree")',
                'button:has-text("Agree")',
            ]

            for selector in cookie_selectors:
                try:
                    button = self.page.locator(selector).first
                    if await button.is_visible(timeout=2000):
                        await button.click()
                        logger.debug(f"Browser {self.browser_id}: Accepted cookies")
                        await BehaviorPatterns.human_delay(1, 2)
                        break
                except:
                    continue

            # Dismiss any other overlays
            try:
                dismiss_selectors = [
                    'button[aria-label*="Dismiss"]',
                    'button[aria-label*="Close"]',
                    '.ytd-popup-container button',
                ]
                for selector in dismiss_selectors:
                    try:
                        button = self.page.locator(selector).first
                        if await button.is_visible(timeout=1000):
                            await button.click()
                            await BehaviorPatterns.human_delay(0.5, 1)
                    except:
                        continue
            except:
                pass

        except Exception as e:
            logger.debug(f"Browser {self.browser_id}: Popup handling error: {e}")

    async def get_video_duration(self) -> float:
        """Get video duration in seconds"""
        try:
            duration = await self.page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    return video ? video.duration : 0;
                }
            """)

            if duration > 0:
                logger.info(f"Browser {self.browser_id}: Video duration is {duration:.1f}s")
                return duration
            else:
                logger.warning(f"Browser {self.browser_id}: Could not detect duration, using default")
                return 180.0  # Default 3 minutes

        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Error getting duration: {e}")
            return 180.0

    async def ensure_video_playing(self):
        """Ensure video is playing"""
        try:
            is_paused = await self.page.evaluate("document.querySelector('video')?.paused || true")
            if is_paused:
                logger.debug(f"Browser {self.browser_id}: Video paused, clicking play")
                await self.page.click('video')
                await BehaviorPatterns.human_delay(0.5, 1)
        except Exception as e:
            logger.debug(f"Browser {self.browser_id}: Error checking video state: {e}")

    async def watch_video(self):
        """Watch video with human-like behavior"""
        try:
            # Get video duration
            duration = await self.get_video_duration()

            # Calculate watch time based on strategy
            watch_percentage = random.uniform(
                Config.MIN_WATCH_PERCENTAGE,
                min(Config.MAX_WATCH_PERCENTAGE, self.strategy['watch_percentage'])
            )
            target_watch_time = duration * watch_percentage

            logger.info(
                f"Browser {self.browser_id}: Will watch {target_watch_time:.1f}s "
                f"({watch_percentage*100:.1f}%) using '{self.strategy['name']}' strategy"
            )

            if self.progress_callback:
                await self.progress_callback(f"Watching video ({watch_percentage*100:.0f}% target)...", 40)

            # Ensure video is playing
            await self.ensure_video_playing()

            # Get behavior sequence for this session
            behavior_sequence = BehaviorPatterns.get_random_behavior_sequence()
            logger.debug(f"Browser {self.browser_id}: Behavior sequence: {behavior_sequence}")

            # Watch video with periodic interactions
            elapsed_time = 0
            behavior_index = 0

            while elapsed_time < target_watch_time:
                # Random check interval
                check_interval = random.uniform(10, 25)
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval

                # Verify video is still playing
                try:
                    current_time = await self.page.evaluate("document.querySelector('video')?.currentTime || 0")
                    is_playing = await self.page.evaluate("!document.querySelector('video')?.paused")

                    if not is_playing:
                        logger.warning(f"Browser {self.browser_id}: Video stopped playing, resuming")
                        await self.page.click('video')
                        await BehaviorPatterns.human_delay(0.5, 1)

                    # Log progress and update UI
                    progress = (current_time / duration) * 100 if duration > 0 else 0
                    watch_progress = min(100, int(40 + (progress * 0.5)))  # Map to 40-90% of overall progress
                    logger.debug(f"Browser {self.browser_id}: Watch progress {progress:.1f}%")

                    if self.progress_callback:
                        await self.progress_callback(
                            f"Watching video... {int(progress)}% of video watched",
                            watch_progress
                        )

                except Exception as e:
                    logger.debug(f"Browser {self.browser_id}: Error checking playback: {e}")

                # Perform random behavior
                if behavior_index < len(behavior_sequence):
                    behavior = behavior_sequence[behavior_index]
                    probability = self._get_behavior_probability(behavior)

                    if random.random() < probability:
                        logger.debug(f"Browser {self.browser_id}: Executing behavior: {behavior}")
                        await BehaviorPatterns.execute_behavior(self.page, behavior)
                        behavior_index += 1

            logger.info(f"Browser {self.browser_id}: Finished watching video")

            if self.progress_callback:
                await self.progress_callback("Finishing up...", 95)

            # Post-watch behavior
            await self._post_watch_behavior()

            return True

        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Error during watch: {e}")
            return False

    def _get_behavior_probability(self, behavior: str) -> float:
        """Get probability for a behavior based on strategy"""
        base_probabilities = {
            'mouse_movement': Config.MOUSE_MOVEMENT_PROBABILITY,
            'scroll': Config.SCROLL_PROBABILITY,
            'pause_resume': Config.PAUSE_RESUME_PROBABILITY,
            'seek': Config.SEEK_PROBABILITY,
            'volume': Config.VOLUME_CHANGE_PROBABILITY,
            'hover': 0.3,
            'comments': 0.2,
            'related_videos': 0.15,
        }

        base_prob = base_probabilities.get(behavior, 0.2)
        multiplier = self.strategy['probability_multiplier']

        return min(1.0, base_prob * multiplier)

    async def _post_watch_behavior(self):
        """Behavior after video finishes"""
        try:
            # Wait a bit
            await BehaviorPatterns.human_delay(2, 5)

            # Random chance to scroll to comments or related videos
            if random.random() < 0.3:
                await BehaviorPatterns.reading_comments(self.page)
            elif random.random() < 0.2:
                await BehaviorPatterns.check_related_videos(self.page)

            # Stay on page for a bit longer
            await BehaviorPatterns.human_delay(2, 4)

        except Exception as e:
            logger.debug(f"Browser {self.browser_id}: Post-watch behavior error: {e}")

    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info(f"Browser {self.browser_id}: Cleaned up")
        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Cleanup error: {e}")

    async def run(self):
        """Main run method"""
        try:
            logger.info(f"Browser {self.browser_id}: Starting")

            # Setup browser
            await self.setup_browser()

            # Navigate to video
            if not await self.navigate_to_video():
                raise Exception("Failed to navigate to video")

            # Handle popups
            await self.handle_popups()

            # Watch video
            success = await self.watch_video()

            if success:
                logger.info(f"Browser {self.browser_id}: Successfully completed")
            else:
                logger.error(f"Browser {self.browser_id}: Failed to complete")

            return success

        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Run error: {e}")

            # Retry logic
            if self.retry_count < Config.MAX_RETRIES:
                self.retry_count += 1
                logger.info(f"Browser {self.browser_id}: Retrying ({self.retry_count}/{Config.MAX_RETRIES})")
                await asyncio.sleep(Config.RETRY_DELAY)
                return await self.run()

            return False

        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    try:
        # Validate configuration
        Config.validate()

        logger.info("="*80)
        logger.info("YouTube Watcher Starting")
        logger.info(f"Video URL: {Config.VIDEO_URL}")
        logger.info(f"Number of browsers: {Config.NUM_BROWSERS}")
        logger.info(f"Headless mode: {Config.HEADLESS}")
        logger.info(f"Proxy enabled: {Config.USE_PROXY}")
        logger.info("="*80)

        # Initialize proxy pool if enabled
        if Config.USE_PROXY:
            logger.info("Initializing proxy pool...")
            ProxyPool.initialize(Config.PROXY_LIST_FILE, Config.PROXY_ROTATION)

            # Test proxies
            proxy_manager = ProxyPool.get_manager()
            if proxy_manager and proxy_manager.proxies:
                logger.info("Testing proxies...")
                working = await proxy_manager.test_all_proxies(concurrent=20)
                if working == 0:
                    logger.warning("No working proxies found! Continuing without proxies...")
                    Config.USE_PROXY = False
                else:
                    logger.info(f"Proxy test complete: {working} working proxies")

        # Create watcher instances
        watchers = []
        for i in range(Config.NUM_BROWSERS):
            watcher = YouTubeWatcher(i, Config.VIDEO_URL)
            watchers.append(watcher)

        # Launch browsers with staggered delays
        tasks = []
        for i, watcher in enumerate(watchers):
            # Stagger launches
            if i > 0:
                delay = random.uniform(Config.LAUNCH_DELAY_MIN, Config.LAUNCH_DELAY_MAX)
                await asyncio.sleep(delay)

            task = asyncio.create_task(watcher.run())
            tasks.append(task)
            logger.info(f"Launched browser {i}")

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Summary
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful

        logger.info("="*80)
        logger.info("Execution Summary")
        logger.info(f"Total browsers: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")

        if Config.USE_PROXY:
            proxy_manager = ProxyPool.get_manager()
            if proxy_manager:
                stats = proxy_manager.get_statistics()
                logger.info(f"Proxy stats: {stats}")

        logger.info("="*80)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Main error: {e}", exc_info=True)
    finally:
        logger.info("YouTube Watcher finished")


if __name__ == "__main__":
    asyncio.run(main())
