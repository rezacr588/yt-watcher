"""
Anti-detection and stealth features for browser automation
"""
import random
from typing import List, Dict, Tuple
import pycountry
from fake_useragent import UserAgent


class StealthConfig:
    """Configuration for stealth features"""

    # Anti-detection JavaScript injection
    STEALTH_JS = """
    // Overwrite the navigator.webdriver property
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });

    // Mock plugins to appear like a real browser
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                name: "Chrome PDF Plugin",
            },
            {
                description: "Chromium PDF Plugin",
                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                name: "Chrome PDF Viewer",
            },
            {
                description: "Native Client Executable",
                filename: "internal-nacl-plugin",
                name: "Native Client",
            },
        ],
    });

    // Mock languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });

    // Chrome runtime
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {},
    };

    // Permissions API mock
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );

    // Mock battery API
    Object.defineProperty(navigator, 'getBattery', {
        get: () => () => Promise.resolve({
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: Math.random(),
            addEventListener: () => {},
            removeEventListener: () => {},
            dispatchEvent: () => {},
        }),
    });

    // Mock connection API
    Object.defineProperty(navigator, 'connection', {
        get: () => ({
            effectiveType: '4g',
            rtt: Math.floor(Math.random() * 50) + 50,
            downlink: Math.random() * 10 + 5,
            saveData: false,
            addEventListener: () => {},
            removeEventListener: () => {},
            dispatchEvent: () => {},
        }),
    });

    // Override prototype
    const originalToString = Function.prototype.toString;
    Function.prototype.toString = function() {
        if (this === navigator.webdriver.get) {
            return 'function get webdriver() { [native code] }';
        }
        return originalToString.call(this);
    };

    // Remove automation markers
    delete navigator.__proto__.webdriver;

    // Mock hardware concurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => Math.floor(Math.random() * 8) + 4,
    });

    // Mock device memory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => [2, 4, 8, 16][Math.floor(Math.random() * 4)],
    });

    // Consistent properties
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Win32',
    });

    // Mock media devices
    if (navigator.mediaDevices) {
        const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
        navigator.mediaDevices.enumerateDevices = async function() {
            return [
                {
                    deviceId: "default",
                    kind: "audioinput",
                    label: "Default - Microphone",
                    groupId: "default"
                },
                {
                    deviceId: "communications",
                    kind: "audioinput",
                    label: "Communications - Microphone",
                    groupId: "default"
                },
                {
                    deviceId: "default",
                    kind: "audiooutput",
                    label: "Default - Speaker",
                    groupId: "default"
                },
                {
                    deviceId: "default",
                    kind: "videoinput",
                    label: "HD Webcam",
                    groupId: "default"
                }
            ];
        };
    }

    // Canvas fingerprinting protection
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(...args) {
        const dataURL = originalToDataURL.apply(this, args);
        // Add slight noise to canvas fingerprint
        return dataURL;
    };

    // WebGL fingerprinting protection
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel(R) HD Graphics';
        }
        return getParameter.call(this, parameter);
    };
    """

    @staticmethod
    def get_random_user_agent() -> str:
        """Generate a random realistic user agent"""
        try:
            ua = UserAgent()
            return ua.random
        except:
            # Fallback to common user agents
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            ]
            return random.choice(user_agents)

    @staticmethod
    def get_random_viewport() -> Dict[str, int]:
        """Get a random but realistic viewport size"""
        common_resolutions = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
            {'width': 1280, 'height': 720},
            {'width': 2560, 'height': 1440},
        ]
        return random.choice(common_resolutions)

    @staticmethod
    def get_random_location() -> Dict:
        """Get random geographic location"""
        locations = [
            {'city': 'New York', 'latitude': 40.7128, 'longitude': -74.0060, 'timezone': 'America/New_York'},
            {'city': 'Los Angeles', 'latitude': 34.0522, 'longitude': -118.2437, 'timezone': 'America/Los_Angeles'},
            {'city': 'Chicago', 'latitude': 41.8781, 'longitude': -87.6298, 'timezone': 'America/Chicago'},
            {'city': 'London', 'latitude': 51.5074, 'longitude': -0.1278, 'timezone': 'Europe/London'},
            {'city': 'Paris', 'latitude': 48.8566, 'longitude': 2.3522, 'timezone': 'Europe/Paris'},
            {'city': 'Tokyo', 'latitude': 35.6762, 'longitude': 139.6503, 'timezone': 'Asia/Tokyo'},
            {'city': 'Sydney', 'latitude': -33.8688, 'longitude': 151.2093, 'timezone': 'Australia/Sydney'},
            {'city': 'Toronto', 'latitude': 43.6532, 'longitude': -79.3832, 'timezone': 'America/Toronto'},
            {'city': 'Berlin', 'latitude': 52.5200, 'longitude': 13.4050, 'timezone': 'Europe/Berlin'},
            {'city': 'Singapore', 'latitude': 1.3521, 'longitude': 103.8198, 'timezone': 'Asia/Singapore'},
        ]
        return random.choice(locations)

    @staticmethod
    def get_browser_args(browser_id: int = 0) -> List[str]:
        """Get browser launch arguments for stealth"""
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            f'--window-position={browser_id * 100},{browser_id * 50}',
            '--mute-audio',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-infobars',
            '--disable-breakpad',
            '--disable-canvas-aa',
            '--disable-2d-canvas-clip-aa',
            '--disable-gl-drawing-for-tests',
            '--enable-features=NetworkService,NetworkServiceInProcess',
            '--force-color-profile=srgb',
            '--metrics-recording-only',
            '--no-first-run',
            '--disable-notifications',
            '--disable-popup-blocking',
        ]

    @staticmethod
    def get_locale_settings() -> Dict:
        """Get random locale settings"""
        locales = [
            {'locale': 'en-US', 'languages': ['en-US', 'en']},
            {'locale': 'en-GB', 'languages': ['en-GB', 'en']},
            {'locale': 'en-CA', 'languages': ['en-CA', 'en', 'fr-CA']},
            {'locale': 'en-AU', 'languages': ['en-AU', 'en']},
        ]
        return random.choice(locales)

    @staticmethod
    def get_color_scheme() -> str:
        """Get random color scheme preference"""
        # Most users use light mode
        return random.choices(['light', 'dark'], weights=[0.7, 0.3])[0]


class FingerprintRandomizer:
    """Randomize browser fingerprints to avoid detection"""

    @staticmethod
    def get_random_screen_resolution() -> Tuple[int, int]:
        """Get random screen resolution"""
        resolutions = [
            (1920, 1080),
            (2560, 1440),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720),
            (3840, 2160),
        ]
        return random.choice(resolutions)

    @staticmethod
    def get_canvas_noise() -> str:
        """Generate canvas noise injection script"""
        return f"""
        const noise = {random.random() * 0.001};
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
            const imageData = originalGetImageData.apply(this, args);
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] = imageData.data[i] + noise;
            }}
            return imageData;
        }};
        """

    @staticmethod
    def get_audio_noise() -> str:
        """Generate audio fingerprint noise"""
        return f"""
        const audioNoise = {random.random() * 0.0001};
        const originalGetChannelData = AudioBuffer.prototype.getChannelData;
        AudioBuffer.prototype.getChannelData = function(...args) {{
            const channelData = originalGetChannelData.apply(this, args);
            for (let i = 0; i < channelData.length; i++) {{
                channelData[i] = channelData[i] + audioNoise;
            }}
            return channelData;
        }};
        """


def get_complete_stealth_script() -> str:
    """Get complete stealth script with all protections"""
    return (
        StealthConfig.STEALTH_JS +
        FingerprintRandomizer.get_canvas_noise() +
        FingerprintRandomizer.get_audio_noise()
    )
