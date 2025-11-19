"""
YouTube Video Watcher with Selenium and Advanced Anti-Detection
WARNING: This tool is for educational purposes only.
Using it to artificially inflate views violates YouTube's Terms of Service.
"""
import asyncio
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import logging
from typing import Optional
import sys
import time

from config import Config
from proxy_manager import ProxyPool, Proxy
from behavior_patterns import BehaviorPatterns, WatchingStrategy
from stealth import StealthConfig

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
    """Main class for watching YouTube videos with human-like behavior using Selenium"""

    def __init__(self, browser_id: int, video_url: str):
        self.browser_id = browser_id
        self.video_url = video_url
        self.driver: Optional[uc.Chrome] = None
        self.proxy: Optional[Proxy] = None
        self.strategy = WatchingStrategy.get_strategy()
        self.retry_count = 0
        self.progress_callback = None  # For UI progress updates

    async def setup_browser(self):
        """Setup browser with stealth configuration using undetected-chromedriver"""
        try:
            logger.info(f"Browser {self.browser_id}: Starting")
            if self.progress_callback:
                await self.progress_callback("Setting up browser...", 5)

            # Configure Chrome options
            options = uc.ChromeOptions()

            # Basic stealth arguments (headless is set in Chrome constructor)
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument(f'--window-size={random.randint(1200, 1920)},{random.randint(800, 1080)}')

            # Random user agent
            if Config.ROTATE_USER_AGENTS:
                user_agent = StealthConfig.get_random_user_agent()
                options.add_argument(f'--user-agent={user_agent}')

            # Proxy configuration
            if Config.USE_PROXY:
                self.proxy = ProxyPool.get_proxy()
                if self.proxy:
                    proxy_string = self.proxy.to_selenium_format()
                    options.add_argument(f'--proxy-server={proxy_string}')
                    logger.info(f"Browser {self.browser_id}: Using proxy {self.proxy.host}:{self.proxy.port}")

            # Create undetected Chrome driver
            # Note: use_subprocess=False helps with stability
            self.driver = uc.Chrome(
                options=options,
                version_main=None,
                use_subprocess=False,
                headless=Config.HEADLESS
            )

            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

            # Maximize window if not headless
            if not Config.HEADLESS:
                self.driver.maximize_window()

            # Execute stealth JavaScript
            if Config.STEALTH_MODE:
                self._inject_stealth_scripts()

            logger.info(f"Browser {self.browser_id}: Setup complete with strategy '{self.strategy['name']}'")

        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Setup error: {e}")
            raise

    def _inject_stealth_scripts(self):
        """Inject stealth JavaScript to mask automation"""
        try:
            # Hide webdriver property
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Mock plugins
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)

            # Mock languages
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)

        except Exception as e:
            logger.debug(f"Browser {self.browser_id}: Stealth injection warning: {e}")

    async def navigate_to_video(self):
        """Navigate to YouTube video with natural browsing pattern"""
        try:
            # First visit YouTube homepage (more natural)
            logger.info(f"Browser {self.browser_id}: Visiting YouTube homepage")
            if self.progress_callback:
                await self.progress_callback("Visiting YouTube homepage...", 10)

            self.driver.get('https://www.youtube.com')
            await self._async_sleep(random.uniform(2, 4))

            # Perform some random scrolling
            if random.random() < 0.5:
                scroll_amount = random.randint(300, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                await self._async_sleep(random.uniform(1, 2))

            # Now navigate to the target video
            logger.info(f"Browser {self.browser_id}: Navigating to video")
            if self.progress_callback:
                await self.progress_callback("Navigating to video...", 20)

            self.driver.get(self.video_url)

            # Wait for page to load
            await self._async_sleep(random.uniform(3, 5))

            # Handle popups
            await self.handle_popups()

            if self.progress_callback:
                await self.progress_callback("Video page loaded", 30)

            return True
        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Navigation error: {e}")
            return False

    async def handle_popups(self):
        """Handle cookie consent and other popups"""
        try:
            # Cookie consent buttons
            cookie_selectors = [
                "//button[contains(@aria-label, 'Accept')]",
                "//button[contains(@aria-label, 'accept')]",
                "//button[contains(text(), 'Accept all')]",
                "//button[contains(text(), 'I agree')]",
                "//tp-yt-paper-button[@aria-label='Reject all']"
            ]

            for selector in cookie_selectors:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    logger.debug(f"Browser {self.browser_id}: Accepted cookies")
                    await self._async_sleep(random.uniform(0.5, 1))
                    break
                except (TimeoutException, NoSuchElementException):
                    continue

        except Exception as e:
            logger.debug(f"Browser {self.browser_id}: Popup handling error: {e}")

    async def get_video_duration(self) -> float:
        """Get video duration in seconds"""
        try:
            # Wait for video element
            logger.debug(f"Browser {self.browser_id}: Waiting for video element...")
            video_element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )

            # Wait for metadata to load
            await self._async_sleep(random.uniform(2, 3))

            # Try multiple times to get duration
            for attempt in range(5):
                duration = self.driver.execute_script("""
                    const video = document.querySelector('video');
                    return video ? video.duration : 0;
                """)

                if duration and duration > 0:
                    logger.info(f"Browser {self.browser_id}: Video duration is {duration:.1f}s")
                    return duration

                logger.debug(f"Browser {self.browser_id}: Duration not ready, attempt {attempt + 1}/5")
                await self._async_sleep(random.uniform(1, 2))

            logger.warning(f"Browser {self.browser_id}: Could not detect duration, using default")
            return 180.0  # Default 3 minutes

        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Error getting duration: {e}")
            return 180.0

    async def ensure_video_playing(self):
        """Ensure video is playing"""
        try:
            # Handle popups first
            await self.handle_popups()

            # Check if video is paused
            is_paused = self.driver.execute_script("""
                const video = document.querySelector('video');
                return video ? video.paused : true;
            """)

            if is_paused:
                logger.debug(f"Browser {self.browser_id}: Video paused, attempting to play")

                # Try clicking the video element
                try:
                    video = self.driver.find_element(By.TAG_NAME, "video")
                    video.click()
                    await self._async_sleep(random.uniform(1, 2))
                except:
                    pass

                # Try clicking play button
                play_button_selectors = [
                    "//button[@aria-label='Play']",
                    "//button[contains(@class, 'ytp-play-button')]",
                    "//button[contains(@class, 'ytp-large-play-button')]"
                ]

                for selector in play_button_selectors:
                    try:
                        button = WebDriverWait(self.driver, 1).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        button.click()
                        logger.debug(f"Browser {self.browser_id}: Clicked play button")
                        await self._async_sleep(random.uniform(1, 2))
                        break
                    except:
                        continue

                # Verify it's playing
                is_still_paused = self.driver.execute_script("""
                    const video = document.querySelector('video');
                    return video ? video.paused : true;
                """)

                if not is_still_paused:
                    logger.info(f"Browser {self.browser_id}: Video is now playing")
                else:
                    logger.warning(f"Browser {self.browser_id}: Video may still be paused")

        except Exception as e:
            logger.debug(f"Browser {self.browser_id}: Error checking video state: {e}")

    async def watch_video_until_near_end(self):
        """Watch video until near the end (90-95%), then it will be refreshed"""
        try:
            # Get video duration
            duration = await self.get_video_duration()

            # Watch 90-95% of video before refreshing (to avoid the end)
            watch_percentage = random.uniform(0.90, 0.95)
            target_watch_time = duration * watch_percentage

            logger.info(
                f"Browser {self.browser_id}: Will watch {target_watch_time:.1f}s "
                f"({watch_percentage*100:.1f}%) before refreshing"
            )

            if self.progress_callback:
                await self.progress_callback(f"Watching video ({watch_percentage*100:.0f}%)...", 40)

            # Ensure video is playing
            await self.ensure_video_playing()

            # Watch the video
            start_time = time.time()
            last_update = start_time

            while (time.time() - start_time) < target_watch_time:
                elapsed = time.time() - start_time

                # Perform random actions
                if random.random() < self.strategy['interaction_probability']:
                    try:
                        action = random.choice(['scroll', 'mouse_move'])
                        if action == 'scroll':
                            scroll_amount = random.randint(-100, 100)
                            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                        await self._async_sleep(random.uniform(0.5, 1))
                    except Exception as e:
                        logger.debug(f"Browser {self.browser_id}: Interaction error: {e}")

                # Progress updates
                if time.time() - last_update > random.uniform(10, 25):
                    progress_percent = 40 + (elapsed / target_watch_time) * 50
                    logger.info(f"Browser {self.browser_id}: Watched {elapsed:.0f}s/{target_watch_time:.0f}s")

                    if self.progress_callback:
                        await self.progress_callback(
                            f"Watching... {elapsed:.0f}s/{target_watch_time:.0f}s",
                            int(progress_percent)
                        )

                    last_update = time.time()

                # Sleep with strategy-specific interval
                await self._async_sleep(random.uniform(2, 5))

            logger.info(f"Browser {self.browser_id}: Near end, will refresh and loop")

            if self.progress_callback:
                await self.progress_callback("Preparing to loop...", 95)

        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Watch error: {e}")

    async def _async_sleep(self, seconds: float):
        """Async sleep wrapper"""
        await asyncio.sleep(seconds)

    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.debug(f"Browser {self.browser_id}: Cleaned up")
        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Cleanup error: {e}")

    async def run(self):
        """Main execution method - runs forever, looping videos"""
        loop_count = 0

        try:
            # Setup browser once
            await self.setup_browser()

            # Loop forever
            while True:
                loop_count += 1
                logger.info(f"Browser {self.browser_id}: Starting loop #{loop_count}")

                try:
                    # Navigate to video
                    if not await self.navigate_to_video():
                        raise Exception("Failed to navigate to video")

                    # Watch video (90-95% of duration)
                    await self.watch_video_until_near_end()

                    # Refresh page for next loop
                    logger.info(f"Browser {self.browser_id}: Refreshing page for loop #{loop_count + 1}")
                    if self.progress_callback:
                        await self.progress_callback(f"Refreshing (Loop #{loop_count})...", 10)

                    await self._async_sleep(random.uniform(2, 4))

                except Exception as e:
                    logger.error(f"Browser {self.browser_id}: Error in loop #{loop_count}: {e}")
                    # Try to recover by refreshing
                    try:
                        self.driver.refresh()
                        await self._async_sleep(random.uniform(3, 5))
                    except:
                        # If refresh fails, recreate browser
                        logger.warning(f"Browser {self.browser_id}: Recreating browser...")
                        await self.cleanup()
                        await self._async_sleep(random.uniform(5, 10))
                        await self.setup_browser()

        except Exception as e:
            logger.error(f"Browser {self.browser_id}: Fatal error: {e}")
            return False

        finally:
            await self.cleanup()

        return False


async def main():
    """Main entry point"""
    watcher = YouTubeWatcher(0, Config.VIDEO_URL)
    await watcher.run()


if __name__ == '__main__':
    asyncio.run(main())
