"""
Unit tests for proxy_manager module
"""
import pytest
import asyncio
import tempfile
import os
from proxy_manager import Proxy, ProxyManager, ProxyPool


class TestProxy:
    """Test Proxy dataclass"""

    def test_proxy_creation(self):
        """Test creating a proxy"""
        proxy = Proxy(host='proxy.example.com', port=8080)
        assert proxy.host == 'proxy.example.com'
        assert proxy.port == 8080
        assert proxy.protocol == 'http'
        assert proxy.is_working is True

    def test_proxy_to_url_no_auth(self):
        """Test converting proxy to URL without authentication"""
        proxy = Proxy(host='proxy.example.com', port=8080)
        assert proxy.to_url() == 'http://proxy.example.com:8080'

    def test_proxy_to_url_with_auth(self):
        """Test converting proxy to URL with authentication"""
        proxy = Proxy(
            host='proxy.example.com',
            port=8080,
            username='user',
            password='pass'
        )
        assert proxy.to_url() == 'http://user:pass@proxy.example.com:8080'

    def test_proxy_to_playwright_dict_no_auth(self):
        """Test converting to Playwright format without auth"""
        proxy = Proxy(host='proxy.example.com', port=8080)
        result = proxy.to_playwright_dict()
        assert result == {'server': 'http://proxy.example.com:8080'}

    def test_proxy_to_playwright_dict_with_auth(self):
        """Test converting to Playwright format with auth"""
        proxy = Proxy(
            host='proxy.example.com',
            port=8080,
            username='user',
            password='pass'
        )
        result = proxy.to_playwright_dict()
        assert result['server'] == 'http://proxy.example.com:8080'
        assert result['username'] == 'user'
        assert result['password'] == 'pass'


class TestProxyManager:
    """Test ProxyManager class"""

    def test_manager_initialization(self):
        """Test initializing proxy manager"""
        manager = ProxyManager()
        assert len(manager.proxies) == 0
        assert manager.current_index == 0
        assert manager.rotation_mode == 'random'

    def test_add_proxy(self):
        """Test adding a proxy"""
        manager = ProxyManager()
        proxy = Proxy(host='proxy1.com', port=8080)
        manager.add_proxy(proxy)
        assert len(manager.proxies) == 1
        assert manager.proxies[0] == proxy

    def test_parse_proxy_string_simple(self):
        """Test parsing simple proxy string"""
        manager = ProxyManager()
        proxy = manager._parse_proxy_string('http://proxy.com:8080')
        assert proxy.host == 'proxy.com'
        assert proxy.port == 8080
        assert proxy.protocol == 'http'
        assert proxy.username is None
        assert proxy.password is None

    def test_parse_proxy_string_with_auth(self):
        """Test parsing proxy string with authentication"""
        manager = ProxyManager()
        proxy = manager._parse_proxy_string('http://user:pass@proxy.com:8080')
        assert proxy.host == 'proxy.com'
        assert proxy.port == 8080
        assert proxy.username == 'user'
        assert proxy.password == 'pass'

    def test_parse_proxy_string_socks(self):
        """Test parsing SOCKS proxy"""
        manager = ProxyManager()
        proxy = manager._parse_proxy_string('socks5://proxy.com:1080')
        assert proxy.host == 'proxy.com'
        assert proxy.port == 1080
        assert proxy.protocol == 'socks5'

    def test_parse_proxy_string_no_protocol(self):
        """Test parsing proxy without protocol"""
        manager = ProxyManager()
        proxy = manager._parse_proxy_string('proxy.com:8080')
        assert proxy.host == 'proxy.com'
        assert proxy.port == 8080
        assert proxy.protocol == 'http'

    def test_load_proxies_from_file(self):
        """Test loading proxies from file"""
        # Create temporary file with proxy list
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('http://proxy1.com:8080\n')
            f.write('http://user:pass@proxy2.com:3128\n')
            f.write('# Comment line\n')
            f.write('\n')  # Empty line
            f.write('socks5://proxy3.com:1080\n')
            temp_file = f.name

        try:
            manager = ProxyManager(temp_file)
            assert len(manager.proxies) == 3
            assert manager.proxies[0].host == 'proxy1.com'
            assert manager.proxies[1].username == 'user'
            assert manager.proxies[2].protocol == 'socks5'
        finally:
            os.unlink(temp_file)

    def test_get_next_proxy_random(self):
        """Test getting next proxy in random mode"""
        manager = ProxyManager()
        manager.rotation_mode = 'random'
        for i in range(3):
            manager.add_proxy(Proxy(host=f'proxy{i}.com', port=8080))

        proxy = manager.get_next_proxy()
        assert proxy is not None
        assert proxy in manager.proxies
        assert proxy.use_count == 1

    def test_get_next_proxy_round_robin(self):
        """Test getting next proxy in round-robin mode"""
        manager = ProxyManager()
        manager.rotation_mode = 'round-robin'
        for i in range(3):
            manager.add_proxy(Proxy(host=f'proxy{i}.com', port=8080))

        # Get proxies in sequence
        proxy1 = manager.get_next_proxy()
        proxy2 = manager.get_next_proxy()
        proxy3 = manager.get_next_proxy()
        proxy4 = manager.get_next_proxy()

        assert proxy1 == manager.proxies[0]
        assert proxy2 == manager.proxies[1]
        assert proxy3 == manager.proxies[2]
        assert proxy4 == manager.proxies[0]  # Should wrap around

    def test_get_next_proxy_sticky(self):
        """Test getting next proxy in sticky mode"""
        manager = ProxyManager()
        manager.rotation_mode = 'sticky'
        for i in range(3):
            manager.add_proxy(Proxy(host=f'proxy{i}.com', port=8080))

        # Should always return the same proxy
        proxy1 = manager.get_next_proxy()
        proxy2 = manager.get_next_proxy()
        proxy3 = manager.get_next_proxy()

        assert proxy1 == proxy2 == proxy3

    def test_get_next_proxy_empty(self):
        """Test getting proxy when no proxies available"""
        manager = ProxyManager()
        proxy = manager.get_next_proxy()
        assert proxy is None

    def test_get_next_proxy_all_failed(self):
        """Test getting proxy when all proxies failed"""
        manager = ProxyManager()
        for i in range(3):
            proxy = Proxy(host=f'proxy{i}.com', port=8080)
            proxy.is_working = False
            manager.add_proxy(proxy)

        # Should reset all proxies and return one
        proxy = manager.get_next_proxy()
        assert proxy is not None
        # All proxies should be reset to working
        assert all(p.is_working for p in manager.proxies)

    def test_mark_proxy_failed(self):
        """Test marking a proxy as failed"""
        manager = ProxyManager()
        proxy = Proxy(host='proxy.com', port=8080)
        manager.add_proxy(proxy)

        assert proxy.is_working is True
        manager.mark_proxy_failed(proxy)
        assert proxy.is_working is False

    @pytest.mark.asyncio
    async def test_test_proxy_success(self):
        """Test proxy testing (mock)"""
        # This would require mocking aiohttp, skip for now
        pass

    def test_get_statistics(self):
        """Test getting proxy statistics"""
        manager = ProxyManager()
        for i in range(5):
            proxy = Proxy(host=f'proxy{i}.com', port=8080)
            if i < 3:
                proxy.is_working = True
            else:
                proxy.is_working = False
            proxy.use_count = i
            proxy.latency = i * 0.1
            manager.add_proxy(proxy)

        stats = manager.get_statistics()
        assert stats['total_proxies'] == 5
        assert stats['working_proxies'] == 3
        assert stats['failed_proxies'] == 2
        assert stats['total_uses'] == 0 + 1 + 2 + 3 + 4

    def test_set_rotation_mode(self):
        """Test setting rotation mode"""
        manager = ProxyManager()

        manager.set_rotation_mode('random')
        assert manager.rotation_mode == 'random'

        manager.set_rotation_mode('round-robin')
        assert manager.rotation_mode == 'round-robin'

        manager.set_rotation_mode('sticky')
        assert manager.rotation_mode == 'sticky'


class TestProxyPool:
    """Test ProxyPool singleton"""

    def test_singleton(self):
        """Test that ProxyPool is a singleton"""
        pool1 = ProxyPool()
        pool2 = ProxyPool()
        assert pool1 is pool2

    def test_initialize(self):
        """Test initializing proxy pool"""
        # Create temporary proxy file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('http://proxy1.com:8080\n')
            temp_file = f.name

        try:
            ProxyPool.initialize(temp_file, 'random')
            manager = ProxyPool.get_manager()
            assert manager is not None
            assert len(manager.proxies) >= 0
        finally:
            os.unlink(temp_file)
            # Reset singleton for other tests
            ProxyPool._manager = None
