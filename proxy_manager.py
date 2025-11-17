"""
Proxy management module for IP rotation and proxy handling
"""
import random
import asyncio
import aiohttp
from typing import List, Optional, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Proxy data structure"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = 'http'
    is_working: bool = True
    latency: float = 0.0
    use_count: int = 0

    def to_url(self) -> str:
        """Convert proxy to URL format"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    def to_playwright_dict(self) -> Dict:
        """Convert to Playwright proxy format"""
        proxy_dict = {
            "server": f"{self.protocol}://{self.host}:{self.port}"
        }
        if self.username and self.password:
            proxy_dict["username"] = self.username
            proxy_dict["password"] = self.password
        return proxy_dict


class ProxyManager:
    """Manages proxy rotation and validation"""

    def __init__(self, proxy_file: Optional[str] = None):
        self.proxies: List[Proxy] = []
        self.current_index = 0
        self.proxy_file = proxy_file
        self.rotation_mode = 'random'  # 'random', 'round-robin', 'sticky'

        if proxy_file:
            self.load_proxies(proxy_file)

    def load_proxies(self, filename: str):
        """
        Load proxies from file
        Format: protocol://username:password@host:port or protocol://host:port
        Example:
            http://proxy1.com:8080
            http://user:pass@proxy2.com:3128
            socks5://user:pass@proxy3.com:1080
        """
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    try:
                        proxy = self._parse_proxy_string(line)
                        if proxy:
                            self.proxies.append(proxy)
                    except Exception as e:
                        logger.warning(f"Failed to parse proxy line '{line}': {e}")

            logger.info(f"Loaded {len(self.proxies)} proxies from {filename}")
        except FileNotFoundError:
            logger.error(f"Proxy file not found: {filename}")
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")

    def _parse_proxy_string(self, proxy_str: str) -> Optional[Proxy]:
        """Parse proxy string into Proxy object"""
        try:
            # Remove protocol if present
            protocol = 'http'
            if '://' in proxy_str:
                protocol, rest = proxy_str.split('://', 1)
            else:
                rest = proxy_str

            # Check for authentication
            username = None
            password = None
            if '@' in rest:
                auth, host_port = rest.rsplit('@', 1)
                if ':' in auth:
                    username, password = auth.split(':', 1)
            else:
                host_port = rest

            # Parse host and port
            if ':' in host_port:
                host, port_str = host_port.rsplit(':', 1)
                port = int(port_str)
            else:
                host = host_port
                port = 8080  # Default port

            return Proxy(
                host=host,
                port=port,
                username=username,
                password=password,
                protocol=protocol
            )
        except Exception as e:
            logger.error(f"Error parsing proxy string '{proxy_str}': {e}")
            return None

    def add_proxy(self, proxy: Proxy):
        """Add a proxy to the pool"""
        self.proxies.append(proxy)

    def get_next_proxy(self) -> Optional[Proxy]:
        """Get next proxy based on rotation mode"""
        if not self.proxies:
            return None

        working_proxies = [p for p in self.proxies if p.is_working]
        if not working_proxies:
            logger.warning("No working proxies available, resetting all proxies")
            for p in self.proxies:
                p.is_working = True
            working_proxies = self.proxies

        if self.rotation_mode == 'random':
            proxy = random.choice(working_proxies)
        elif self.rotation_mode == 'round-robin':
            proxy = working_proxies[self.current_index % len(working_proxies)]
            self.current_index += 1
        else:  # sticky - use same proxy
            proxy = working_proxies[0]

        proxy.use_count += 1
        return proxy

    async def test_proxy(self, proxy: Proxy, test_url: str = "https://www.google.com", timeout: int = 10) -> bool:
        """Test if a proxy is working"""
        try:
            start_time = asyncio.get_event_loop().time()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy.to_url(),
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        proxy.latency = asyncio.get_event_loop().time() - start_time
                        proxy.is_working = True
                        logger.info(f"Proxy {proxy.host}:{proxy.port} is working (latency: {proxy.latency:.2f}s)")
                        return True

            proxy.is_working = False
            return False
        except Exception as e:
            logger.debug(f"Proxy {proxy.host}:{proxy.port} failed: {e}")
            proxy.is_working = False
            return False

    async def test_all_proxies(self, concurrent: int = 10) -> int:
        """Test all proxies concurrently"""
        logger.info(f"Testing {len(self.proxies)} proxies...")

        semaphore = asyncio.Semaphore(concurrent)

        async def test_with_semaphore(proxy):
            async with semaphore:
                return await self.test_proxy(proxy)

        results = await asyncio.gather(*[test_with_semaphore(p) for p in self.proxies])

        working_count = sum(results)
        logger.info(f"Proxy test complete: {working_count}/{len(self.proxies)} working")
        return working_count

    def mark_proxy_failed(self, proxy: Proxy):
        """Mark a proxy as failed"""
        proxy.is_working = False
        logger.warning(f"Marked proxy {proxy.host}:{proxy.port} as failed")

    def get_statistics(self) -> Dict:
        """Get proxy usage statistics"""
        total = len(self.proxies)
        working = sum(1 for p in self.proxies if p.is_working)
        total_uses = sum(p.use_count for p in self.proxies)

        return {
            'total_proxies': total,
            'working_proxies': working,
            'failed_proxies': total - working,
            'total_uses': total_uses,
            'average_latency': sum(p.latency for p in self.proxies if p.is_working) / max(working, 1)
        }

    def set_rotation_mode(self, mode: str):
        """Set proxy rotation mode"""
        if mode in ['random', 'round-robin', 'sticky']:
            self.rotation_mode = mode
            logger.info(f"Proxy rotation mode set to: {mode}")
        else:
            logger.warning(f"Invalid rotation mode: {mode}")


class ProxyPool:
    """Singleton proxy pool for sharing proxies across instances"""
    _instance = None
    _manager: Optional[ProxyManager] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, proxy_file: str, rotation_mode: str = 'random'):
        """Initialize the proxy pool"""
        if cls._manager is None:
            cls._manager = ProxyManager(proxy_file)
            cls._manager.set_rotation_mode(rotation_mode)

    @classmethod
    def get_proxy(cls) -> Optional[Proxy]:
        """Get a proxy from the pool"""
        if cls._manager is None:
            return None
        return cls._manager.get_next_proxy()

    @classmethod
    def get_manager(cls) -> Optional[ProxyManager]:
        """Get the proxy manager instance"""
        return cls._manager
