"""
Sophisticated human behavior simulation patterns
"""
import random
import asyncio
from typing import Tuple, List
import math
import logging

logger = logging.getLogger(__name__)


class BehaviorPatterns:
    """Simulates realistic human browsing behavior"""

    @staticmethod
    async def human_delay(min_seconds: float = 1, max_seconds: float = 3):
        """Random delay with natural distribution (slightly favors middle values)"""
        # Use beta distribution for more natural timing
        delay = min_seconds + (max_seconds - min_seconds) * random.betavariate(2, 2)
        await asyncio.sleep(delay)

    @staticmethod
    async def natural_mouse_movement(page, from_x: int, from_y: int, to_x: int, to_y: int, steps: int = None):
        """
        Simulate natural mouse movement with bezier curve
        Humans don't move mouse in straight lines
        """
        if steps is None:
            # More steps for longer distances
            distance = math.sqrt((to_x - from_x)**2 + (to_y - from_y)**2)
            steps = max(10, int(distance / 10))

        # Generate control points for bezier curve
        ctrl_x1 = random.randint(min(from_x, to_x), max(from_x, to_x))
        ctrl_y1 = random.randint(min(from_y, to_y), max(from_y, to_y))

        for i in range(steps + 1):
            t = i / steps
            # Cubic bezier curve formula
            x = int((1-t)**3 * from_x + 3*(1-t)**2*t * ctrl_x1 + 3*(1-t)*t**2 * to_x + t**3 * to_x)
            y = int((1-t)**3 * from_y + 3*(1-t)**2*t * ctrl_y1 + 3*(1-t)*t**2 * to_y + t**3 * to_y)

            try:
                await page.mouse.move(x, y)
                # Small random delay between movements
                await asyncio.sleep(random.uniform(0.001, 0.005))
            except:
                pass

    @staticmethod
    async def random_mouse_movements(page, count: int = None):
        """Perform random mouse movements on the page"""
        if count is None:
            count = random.randint(2, 5)

        try:
            width = await page.evaluate("window.innerWidth")
            height = await page.evaluate("window.innerHeight")

            current_x, current_y = width // 2, height // 2

            for _ in range(count):
                # Avoid edges
                target_x = random.randint(100, width - 100)
                target_y = random.randint(100, height - 100)

                await BehaviorPatterns.natural_mouse_movement(
                    page, current_x, current_y, target_x, target_y
                )

                current_x, current_y = target_x, target_y
                await asyncio.sleep(random.uniform(0.1, 0.3))

        except Exception as e:
            logger.debug(f"Mouse movement error: {e}")

    @staticmethod
    async def scroll_behavior(page):
        """Simulate human-like scrolling patterns"""
        try:
            # Random scroll patterns
            patterns = [
                # Small scroll down
                lambda: page.mouse.wheel(0, random.randint(100, 300)),
                # Small scroll up
                lambda: page.mouse.wheel(0, random.randint(-300, -100)),
                # Read and scroll (multiple small scrolls)
                lambda: BehaviorPatterns._reading_scroll(page),
                # Quick scroll to comments section
                lambda: page.mouse.wheel(0, random.randint(500, 1000)),
            ]

            pattern = random.choice(patterns)
            await pattern()
            await BehaviorPatterns.human_delay(0.5, 1.5)

        except Exception as e:
            logger.debug(f"Scroll behavior error: {e}")

    @staticmethod
    async def _reading_scroll(page):
        """Simulate reading behavior with multiple small scrolls"""
        num_scrolls = random.randint(2, 5)
        for _ in range(num_scrolls):
            await page.mouse.wheel(0, random.randint(50, 150))
            await asyncio.sleep(random.uniform(1, 3))  # Pause to "read"

    @staticmethod
    async def video_player_interaction(page, action: str = None):
        """
        Simulate interactions with video player
        Actions: pause, play, seek, volume, quality, fullscreen
        """
        try:
            if action is None:
                action = random.choice(['pause_resume', 'seek', 'volume', 'hover'])

            if action == 'pause_resume':
                await BehaviorPatterns._pause_and_resume(page)
            elif action == 'seek':
                await BehaviorPatterns._seek_video(page)
            elif action == 'volume':
                await BehaviorPatterns._adjust_volume(page)
            elif action == 'hover':
                await BehaviorPatterns._hover_player(page)

        except Exception as e:
            logger.debug(f"Video interaction error ({action}): {e}")

    @staticmethod
    async def _pause_and_resume(page):
        """Pause video briefly then resume"""
        try:
            # Click on video to pause
            video = page.locator('video').first
            if await video.count() > 0:
                await video.click()
                logger.debug("Paused video")
                await BehaviorPatterns.human_delay(2, 6)  # Pause for a few seconds
                await video.click()
                logger.debug("Resumed video")
        except Exception as e:
            logger.debug(f"Pause/resume error: {e}")

    @staticmethod
    async def _seek_video(page):
        """Seek to a random position in the video"""
        try:
            # Get current time and duration
            current_time = await page.evaluate("document.querySelector('video')?.currentTime || 0")
            duration = await page.evaluate("document.querySelector('video')?.duration || 0")

            if duration > 0:
                # Seek within +/- 30 seconds or 10% of duration
                seek_range = min(30, duration * 0.1)
                new_time = current_time + random.uniform(-seek_range, seek_range)
                new_time = max(0, min(new_time, duration))

                await page.evaluate(f"document.querySelector('video').currentTime = {new_time}")
                logger.debug(f"Seeked video to {new_time:.1f}s")

        except Exception as e:
            logger.debug(f"Seek error: {e}")

    @staticmethod
    async def _adjust_volume(page):
        """Randomly adjust video volume"""
        try:
            new_volume = random.uniform(0.3, 0.8)
            await page.evaluate(f"document.querySelector('video').volume = {new_volume}")
            logger.debug(f"Adjusted volume to {new_volume:.2f}")
        except Exception as e:
            logger.debug(f"Volume adjustment error: {e}")

    @staticmethod
    async def _hover_player(page):
        """Hover over video player to reveal controls"""
        try:
            video = page.locator('video').first
            if await video.count() > 0:
                box = await video.bounding_box()
                if box:
                    hover_x = box['x'] + box['width'] / 2
                    hover_y = box['y'] + box['height'] / 2
                    await page.mouse.move(hover_x, hover_y)
                    await BehaviorPatterns.human_delay(1, 2)
        except Exception as e:
            logger.debug(f"Hover error: {e}")

    @staticmethod
    async def reading_comments(page):
        """Simulate reading comments section"""
        try:
            # Scroll to comments
            await page.mouse.wheel(0, random.randint(1000, 1500))
            await BehaviorPatterns.human_delay(1, 2)

            # Read a few comments (multiple small scrolls)
            for _ in range(random.randint(2, 5)):
                await page.mouse.wheel(0, random.randint(100, 300))
                await BehaviorPatterns.human_delay(2, 4)  # Time to "read"

            # Scroll back up
            await page.mouse.wheel(0, random.randint(-1500, -1000))

        except Exception as e:
            logger.debug(f"Comment reading error: {e}")

    @staticmethod
    async def check_related_videos(page):
        """Simulate looking at related videos sidebar"""
        try:
            # Move mouse to right side where related videos are
            width = await page.evaluate("window.innerWidth")
            height = await page.evaluate("window.innerHeight")

            # Move to right sidebar area
            x = random.randint(int(width * 0.75), int(width * 0.95))
            y = random.randint(200, height - 200)

            await BehaviorPatterns.natural_mouse_movement(
                page,
                width // 2, height // 2,  # From center
                x, y
            )

            # Hover over a few video suggestions
            for _ in range(random.randint(1, 3)):
                y += random.randint(150, 250)
                await page.mouse.move(x, y)
                await BehaviorPatterns.human_delay(0.5, 1.5)

        except Exception as e:
            logger.debug(f"Related videos check error: {e}")

    @staticmethod
    def get_random_behavior_sequence() -> List[str]:
        """Get a random sequence of behaviors to perform during watch session"""
        all_behaviors = [
            'mouse_movement',
            'scroll',
            'pause_resume',
            'seek',
            'volume',
            'hover',
            'comments',
            'related_videos',
        ]

        # Select random subset
        num_behaviors = random.randint(2, 5)
        return random.sample(all_behaviors, num_behaviors)

    @staticmethod
    async def execute_behavior(page, behavior: str):
        """Execute a specific behavior"""
        behavior_map = {
            'mouse_movement': lambda: BehaviorPatterns.random_mouse_movements(page),
            'scroll': lambda: BehaviorPatterns.scroll_behavior(page),
            'pause_resume': lambda: BehaviorPatterns.video_player_interaction(page, 'pause_resume'),
            'seek': lambda: BehaviorPatterns.video_player_interaction(page, 'seek'),
            'volume': lambda: BehaviorPatterns.video_player_interaction(page, 'volume'),
            'hover': lambda: BehaviorPatterns.video_player_interaction(page, 'hover'),
            'comments': lambda: BehaviorPatterns.reading_comments(page),
            'related_videos': lambda: BehaviorPatterns.check_related_videos(page),
        }

        handler = behavior_map.get(behavior)
        if handler:
            try:
                await handler()
            except Exception as e:
                logger.debug(f"Error executing behavior {behavior}: {e}")


class WatchingStrategy:
    """Different watching strategies to vary behavior"""

    @staticmethod
    def get_strategy() -> dict:
        """Get a random watching strategy"""
        strategies = [
            {
                'name': 'casual_viewer',
                'watch_percentage': random.uniform(0.6, 0.8),
                'interaction_frequency': 'low',
                'probability_multiplier': 0.5,
            },
            {
                'name': 'engaged_viewer',
                'watch_percentage': random.uniform(0.9, 1.0),
                'interaction_frequency': 'high',
                'probability_multiplier': 1.5,
            },
            {
                'name': 'quick_viewer',
                'watch_percentage': random.uniform(0.3, 0.5),
                'interaction_frequency': 'very_low',
                'probability_multiplier': 0.3,
            },
            {
                'name': 'binge_watcher',
                'watch_percentage': 1.0,
                'interaction_frequency': 'medium',
                'probability_multiplier': 1.0,
            },
        ]

        return random.choice(strategies)
