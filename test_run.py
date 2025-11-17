"""
Quick test script to verify the application can initialize
"""
import sys
from config import Config
from proxy_manager import ProxyManager
from behavior_patterns import BehaviorPatterns, WatchingStrategy
from stealth import StealthConfig, get_complete_stealth_script
from youtube_watcher import YouTubeWatcher

def test_configuration():
    """Test configuration loads correctly"""
    print("Testing configuration...")
    try:
        Config.validate()
        print(f"✓ Configuration valid")
        print(f"  - Video URL: {Config.VIDEO_URL}")
        print(f"  - Num browsers: {Config.NUM_BROWSERS}")
        print(f"  - Headless: {Config.HEADLESS}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_proxy_manager():
    """Test proxy manager initializes"""
    print("\nTesting proxy manager...")
    try:
        manager = ProxyManager()
        print(f"✓ Proxy manager initialized")
        print(f"  - Proxies loaded: {len(manager.proxies)}")
        return True
    except Exception as e:
        print(f"✗ Proxy manager error: {e}")
        return False

def test_behavior_patterns():
    """Test behavior patterns"""
    print("\nTesting behavior patterns...")
    try:
        strategy = WatchingStrategy.get_strategy()
        behaviors = BehaviorPatterns.get_random_behavior_sequence()
        print(f"✓ Behavior patterns working")
        print(f"  - Strategy: {strategy['name']}")
        print(f"  - Behaviors: {len(behaviors)}")
        return True
    except Exception as e:
        print(f"✗ Behavior patterns error: {e}")
        return False

def test_stealth_config():
    """Test stealth configuration"""
    print("\nTesting stealth configuration...")
    try:
        ua = StealthConfig.get_random_user_agent()
        viewport = StealthConfig.get_random_viewport()
        script = get_complete_stealth_script()
        print(f"✓ Stealth config working")
        print(f"  - User agent length: {len(ua)}")
        print(f"  - Viewport: {viewport['width']}x{viewport['height']}")
        print(f"  - Stealth script length: {len(script)}")
        return True
    except Exception as e:
        print(f"✗ Stealth config error: {e}")
        return False

def test_watcher_initialization():
    """Test watcher can be initialized"""
    print("\nTesting watcher initialization...")
    try:
        watcher = YouTubeWatcher(0, Config.VIDEO_URL)
        print(f"✓ Watcher initialized")
        print(f"  - Browser ID: {watcher.browser_id}")
        print(f"  - Strategy: {watcher.strategy['name']}")
        return True
    except Exception as e:
        print(f"✗ Watcher initialization error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("YouTube Watcher - Quick Test")
    print("="*60)

    tests = [
        test_configuration,
        test_proxy_manager,
        test_behavior_patterns,
        test_stealth_config,
        test_watcher_initialization,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "="*60)
    print("Test Results")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All components initialized successfully!")
        print("The application is ready to use.")
        return 0
    else:
        print("\n✗ Some components failed to initialize.")
        print("Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
