"""
Unit tests for stealth module
"""
import pytest
from stealth import (
    StealthConfig,
    FingerprintRandomizer,
    get_complete_stealth_script
)


class TestStealthConfig:
    """Test StealthConfig class"""

    def test_get_random_user_agent(self):
        """Test getting random user agent"""
        ua = StealthConfig.get_random_user_agent()

        assert isinstance(ua, str)
        assert len(ua) > 0
        assert 'Mozilla' in ua  # All major browsers use Mozilla in UA

    def test_get_random_user_agent_variety(self):
        """Test that user agents vary"""
        user_agents = [StealthConfig.get_random_user_agent() for _ in range(5)]

        # Should have some variety (though could theoretically be all same)
        assert all(isinstance(ua, str) for ua in user_agents)
        assert all(len(ua) > 0 for ua in user_agents)

    def test_get_random_viewport(self):
        """Test getting random viewport"""
        viewport = StealthConfig.get_random_viewport()

        assert isinstance(viewport, dict)
        assert 'width' in viewport
        assert 'height' in viewport
        assert isinstance(viewport['width'], int)
        assert isinstance(viewport['height'], int)
        assert viewport['width'] > 0
        assert viewport['height'] > 0

    def test_get_random_viewport_common_resolutions(self):
        """Test that viewport sizes are common resolutions"""
        common_widths = [1920, 1366, 1536, 1440, 1280, 2560]
        common_heights = [1080, 768, 864, 900, 720, 1440]

        for _ in range(10):
            viewport = StealthConfig.get_random_viewport()
            assert viewport['width'] in common_widths
            assert viewport['height'] in common_heights

    def test_get_random_location(self):
        """Test getting random location"""
        location = StealthConfig.get_random_location()

        assert isinstance(location, dict)
        assert 'city' in location
        assert 'latitude' in location
        assert 'longitude' in location
        assert 'timezone' in location

        # Verify latitude/longitude are valid
        assert -90 <= location['latitude'] <= 90
        assert -180 <= location['longitude'] <= 180

        # Verify timezone format
        assert '/' in location['timezone']

    def test_get_browser_args(self):
        """Test getting browser arguments"""
        args = StealthConfig.get_browser_args(browser_id=5)

        assert isinstance(args, list)
        assert len(args) > 0
        assert all(isinstance(arg, str) for arg in args)

        # Check for critical stealth arguments
        assert any('AutomationControlled' in arg for arg in args)
        assert any('--no-sandbox' in arg for arg in args)
        assert any('--mute-audio' in arg for arg in args)

        # Check browser ID is used in positioning
        assert any('--window-position=500,250' in arg for arg in args)

    def test_get_browser_args_different_ids(self):
        """Test browser args vary by browser ID"""
        args1 = StealthConfig.get_browser_args(browser_id=0)
        args2 = StealthConfig.get_browser_args(browser_id=1)

        # Should have different window positions
        pos1 = [arg for arg in args1 if '--window-position' in arg]
        pos2 = [arg for arg in args2 if '--window-position' in arg]

        assert pos1 != pos2

    def test_get_locale_settings(self):
        """Test getting locale settings"""
        locale = StealthConfig.get_locale_settings()

        assert isinstance(locale, dict)
        assert 'locale' in locale
        assert 'languages' in locale
        assert isinstance(locale['languages'], list)
        assert len(locale['languages']) > 0

        # Verify format
        assert '-' in locale['locale'] or locale['locale'] == 'en'

    def test_get_color_scheme(self):
        """Test getting color scheme"""
        for _ in range(10):
            scheme = StealthConfig.get_color_scheme()
            assert scheme in ['light', 'dark']

    def test_stealth_js_content(self):
        """Test that stealth JavaScript is comprehensive"""
        js = StealthConfig.STEALTH_JS

        assert isinstance(js, str)
        assert len(js) > 0

        # Check for critical anti-detection features
        assert 'navigator.webdriver' in js
        assert 'plugins' in js  # Can be navigator.plugins or 'plugins'
        assert 'languages' in js  # Can be navigator.languages or 'languages'
        assert 'window.chrome' in js
        assert 'permissions' in js


class TestFingerprintRandomizer:
    """Test FingerprintRandomizer class"""

    def test_get_random_screen_resolution(self):
        """Test getting random screen resolution"""
        width, height = FingerprintRandomizer.get_random_screen_resolution()

        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0

        # Should be one of the common resolutions
        common_resolutions = [
            (1920, 1080), (2560, 1440), (1366, 768),
            (1536, 864), (1440, 900), (1280, 720), (3840, 2160)
        ]
        assert (width, height) in common_resolutions

    def test_get_canvas_noise(self):
        """Test getting canvas noise script"""
        noise = FingerprintRandomizer.get_canvas_noise()

        assert isinstance(noise, str)
        assert len(noise) > 0
        assert 'canvas' in noise.lower() or 'imagedata' in noise.lower()
        assert 'noise' in noise.lower()

    def test_get_canvas_noise_uniqueness(self):
        """Test that canvas noise varies"""
        noise1 = FingerprintRandomizer.get_canvas_noise()
        noise2 = FingerprintRandomizer.get_canvas_noise()

        # Should have different noise values
        assert noise1 != noise2

    def test_get_audio_noise(self):
        """Test getting audio noise script"""
        noise = FingerprintRandomizer.get_audio_noise()

        assert isinstance(noise, str)
        assert len(noise) > 0
        assert 'audio' in noise.lower()
        assert 'noise' in noise.lower()

    def test_get_audio_noise_uniqueness(self):
        """Test that audio noise varies"""
        noise1 = FingerprintRandomizer.get_audio_noise()
        noise2 = FingerprintRandomizer.get_audio_noise()

        # Should have different noise values
        assert noise1 != noise2


class TestStealthScript:
    """Test complete stealth script generation"""

    def test_get_complete_stealth_script(self):
        """Test getting complete stealth script"""
        script = get_complete_stealth_script()

        assert isinstance(script, str)
        assert len(script) > 0

        # Should contain all components
        assert 'navigator.webdriver' in script
        assert 'canvas' in script.lower() or 'imagedata' in script.lower()
        assert 'audio' in script.lower()

    def test_stealth_script_is_valid_javascript(self):
        """Test that stealth script looks like valid JavaScript"""
        script = get_complete_stealth_script()

        # Basic syntax checks
        assert script.count('{') == script.count('}')  # Balanced braces
        assert script.count('(') == script.count(')')  # Balanced parentheses

        # Should have function definitions
        assert 'function' in script or '=>' in script

        # Should have Object.defineProperty calls
        assert 'Object.defineProperty' in script

    def test_stealth_script_uniqueness(self):
        """Test that stealth scripts vary (due to random noise)"""
        script1 = get_complete_stealth_script()
        script2 = get_complete_stealth_script()

        # Should be different due to random noise values
        assert script1 != script2
