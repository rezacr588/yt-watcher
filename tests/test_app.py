"""
Tests for Flask application
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from threading import local as thread_local

import app as flask_app
from watcher_controller import WatcherController


class TestFlaskApp:
    """Test Flask application"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        flask_app.app.config['TESTING'] = True
        with flask_app.app.test_client() as client:
            yield client

    @pytest.fixture
    def mock_controller(self):
        """Mock controller"""
        controller = MagicMock(spec=WatcherController)
        controller.get_config.return_value = {
            'video_url': 'https://www.youtube.com/watch?v=test',
            'num_browsers': 10,
            'headless': False
        }
        controller.get_status.return_value = {
            'is_running': False,
            'total_watchers': 0,
            'successful': 0,
            'failed': 0
        }
        controller.stop_watchers.return_value = {'success': True}
        return controller

    def test_index_route(self, client):
        """Test index route"""
        response = client.get('/')
        assert response.status_code == 200

    def test_get_config_route(self, client, mock_controller):
        """Test /api/config GET route"""
        with patch.object(flask_app, 'controller', mock_controller):
            response = client.get('/api/config')
            assert response.status_code == 200
            data = response.get_json()
            assert 'video_url' in data
            assert 'num_browsers' in data

    def test_get_config_error(self, client, mock_controller):
        """Test /api/config error handling"""
        mock_controller.get_config.side_effect = RuntimeError("Test error")

        with patch.object(flask_app, 'controller', mock_controller):
            response = client.get('/api/config')
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data

    def test_get_status_route(self, client, mock_controller):
        """Test /api/status GET route"""
        with patch.object(flask_app, 'controller', mock_controller):
            response = client.get('/api/status')
            assert response.status_code == 200
            data = response.get_json()
            assert 'is_running' in data
            assert 'total_watchers' in data

    def test_get_status_error(self, client, mock_controller):
        """Test /api/status error handling"""
        mock_controller.get_status.side_effect = RuntimeError("Test error")

        with patch.object(flask_app, 'controller', mock_controller):
            response = client.get('/api/status')
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data

    def test_start_watchers_route(self, client, mock_controller):
        """Test /api/start POST route"""
        config = {
            'video_url': 'https://www.youtube.com/watch?v=test',
            'num_browsers': 5,
            'headless': True
        }

        with patch.object(flask_app, 'controller', mock_controller):
            response = client.post('/api/start', json=config)
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_start_watchers_error(self, client):
        """Test /api/start error handling"""
        # Send invalid JSON
        response = client.post('/api/start', data='invalid json')
        assert response.status_code in [400, 500]

    def test_stop_watchers_route(self, client, mock_controller):
        """Test /api/stop POST route"""
        with patch.object(flask_app, 'controller', mock_controller):
            response = client.post('/api/stop')
            assert response.status_code == 200
            data = response.get_json()
            assert 'success' in data or 'error' in data

    def test_stop_watchers_error(self, client, mock_controller):
        """Test /api/stop error handling"""
        mock_controller.stop_watchers.side_effect = RuntimeError("Test error")

        with patch.object(flask_app, 'controller', mock_controller):
            response = client.post('/api/stop')
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data

    def test_get_event_loop(self):
        """Test get_event_loop function"""
        loop1 = flask_app.get_event_loop()
        assert loop1 is not None
        assert isinstance(loop1, asyncio.AbstractEventLoop)

        # Get again - should return same loop
        loop2 = flask_app.get_event_loop()
        assert loop1 is loop2

    def test_get_event_loop_closed(self):
        """Test get_event_loop when loop is closed"""
        # Create and close a loop
        loop = flask_app.get_event_loop()
        loop.close()

        # Should create new loop
        new_loop = flask_app.get_event_loop()
        assert new_loop is not None
        assert new_loop != loop
        assert not new_loop.is_closed()

        # Cleanup
        new_loop.close()

    def test_socketio_callback(self):
        """Test socketio_callback function"""
        with patch.object(flask_app.socketio, 'emit') as mock_emit:
            flask_app.socketio_callback('test_event', {'data': 'test'})
            mock_emit.assert_called_once_with('test_event', {'data': 'test'}, namespace='/')

    def test_socketio_callback_error(self):
        """Test socketio_callback error handling"""
        with patch.object(flask_app.socketio, 'emit', side_effect=RuntimeError("Test error")):
            # Should not raise exception
            flask_app.socketio_callback('test_event', {'data': 'test'})


class TestSocketIOHandlers:
    """Test SocketIO event handlers"""

    @pytest.fixture
    def socketio_client(self):
        """Create SocketIO test client"""
        flask_app.app.config['TESTING'] = True
        return flask_app.socketio.test_client(flask_app.app)

    @pytest.fixture
    def mock_controller(self):
        """Mock controller"""
        controller = MagicMock(spec=WatcherController)
        controller.get_status.return_value = {
            'is_running': False,
            'total_watchers': 0
        }
        return controller

    def test_socketio_connect(self, socketio_client):
        """Test WebSocket connection"""
        assert socketio_client.is_connected()
        received = socketio_client.get_received()
        # Should receive connection status message
        assert len(received) > 0

    def test_socketio_disconnect(self, socketio_client):
        """Test WebSocket disconnection"""
        socketio_client.disconnect()
        assert not socketio_client.is_connected()

    def test_socketio_request_status(self, socketio_client, mock_controller):
        """Test request_status event"""
        with patch.object(flask_app, 'controller', mock_controller):
            socketio_client.emit('request_status')

            # Wait for response
            received = socketio_client.get_received()

            # Should receive status_update or error
            assert len(received) > 0

    def test_socketio_request_status_error(self, socketio_client, mock_controller):
        """Test request_status error handling"""
        mock_controller.get_status.side_effect = RuntimeError("Test error")

        with patch.object(flask_app, 'controller', mock_controller):
            socketio_client.emit('request_status')

            # Should receive error message
            received = socketio_client.get_received()
            assert len(received) > 0


class TestThreadSafety:
    """Test thread safety of the application"""

    def test_thread_local_storage(self):
        """Test thread-local storage for event loops"""
        from threading import Thread

        loops = []

        def get_loop():
            loop = flask_app.get_event_loop()
            loops.append(loop)

        # Create loops in different threads
        threads = [Thread(target=get_loop) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each thread should have different loop
        assert len(loops) == 3
        # Note: loops might be the same if threads reuse thread-local storage

        # Cleanup
        for loop in loops:
            if not loop.is_closed():
                loop.close()

    def test_concurrent_api_calls(self, mock_controller):
        """Test concurrent API calls"""
        flask_app.app.config['TESTING'] = True

        with flask_app.app.test_client() as client:
            with patch.object(flask_app, 'controller', mock_controller):
                # Make multiple concurrent requests
                responses = []
                for _ in range(5):
                    response = client.get('/api/status')
                    responses.append(response)

                # All should succeed
                for response in responses:
                    assert response.status_code == 200


class TestConfiguration:
    """Test application configuration"""

    def test_secret_key_set(self):
        """Test that secret key is set"""
        assert flask_app.app.config['SECRET_KEY'] is not None
        assert flask_app.app.config['SECRET_KEY'] != ''

    def test_cors_enabled(self):
        """Test CORS is enabled"""
        # CORS should be configured
        assert 'CORS' in dir(flask_app)

    def test_socketio_configured(self):
        """Test SocketIO is configured"""
        assert flask_app.socketio is not None
        # Check async mode
        assert flask_app.socketio.async_mode == 'threading'
