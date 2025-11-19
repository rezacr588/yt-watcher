"""
Flask application for YouTube Watcher UI
"""
import asyncio
import logging
import os
from threading import Thread, local
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv

from watcher_controller import WatcherController

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'youtube-watcher-secret-key-change-me')
if app.config['SECRET_KEY'] == 'youtube-watcher-secret-key-change-me':
    logger.warning("Using default SECRET_KEY! Set FLASK_SECRET_KEY in .env for production")
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Create controller
controller = WatcherController()

# Thread-local storage for event loops
thread_local = local()


def get_event_loop():
    """Get or create event loop for this thread"""
    if not hasattr(thread_local, 'loop') or thread_local.loop.is_closed():
        thread_local.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(thread_local.loop)
    return thread_local.loop


def socketio_callback(event_type, data):
    """Callback for controller to emit updates via SocketIO"""
    try:
        socketio.emit(event_type, data, namespace='/')
    except Exception as e:
        logger.error(f"SocketIO emit error: {e}")


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        config = controller.get_config()
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current watcher status"""
    try:
        status = controller.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/start', methods=['POST'])
def start_watchers():
    """Start watchers with configuration"""
    try:
        config = request.json
        logger.info(f"Starting watchers with config: {config}")

        # Run in background thread
        def run_async():
            event_loop = get_event_loop()
            event_loop.run_until_complete(
                controller.start_watchers(config, callback=socketio_callback)
            )

        thread = Thread(target=run_async)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'Watchers starting...'})

    except Exception as e:
        logger.error(f"Error starting watchers: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def stop_watchers():
    """Stop all watchers"""
    try:
        result = controller.stop_watchers()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping watchers: {e}")
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'message': 'Connected to server', 'type': 'success'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client"""
    try:
        status = controller.get_status()
        emit('status_update', status)
    except Exception as e:
        logger.error(f"Error handling status request: {e}")
        emit('status', {'message': f'Error: {str(e)}', 'type': 'error'})


if __name__ == '__main__':
    logger.info("Starting YouTube Watcher UI...")
    logger.info("Open http://localhost:5001 in your browser")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
