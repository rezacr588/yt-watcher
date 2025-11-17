// YouTube Watcher UI JavaScript

class WatcherUI {
    constructor() {
        this.socket = null;
        this.watchers = {};
        this.isRunning = false;
        this.startTime = null;
        this.elapsedInterval = null;

        this.init();
    }

    init() {
        // Initialize Socket.IO
        this.socket = io();

        // Setup socket event listeners
        this.setupSocketListeners();

        // Setup UI event listeners
        this.setupUIListeners();

        // Load current configuration
        this.loadConfiguration();
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.addStatusMessage('Connected to server', 'success');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.addStatusMessage('Disconnected from server', 'error');
        });

        this.socket.on('status', (data) => {
            this.addStatusMessage(data.message, data.type);
        });

        this.socket.on('watcher_update', (data) => {
            this.updateWatcher(data);
        });

        this.socket.on('status_update', (data) => {
            this.updateStatus(data);
        });
    }

    setupUIListeners() {
        // Start button
        document.getElementById('start-btn').addEventListener('click', () => {
            this.startWatchers();
        });

        // Stop button
        document.getElementById('stop-btn').addEventListener('click', () => {
            this.stopWatchers();
        });
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();

            // Populate form fields
            document.getElementById('video_url').value = config.video_url || '';
            document.getElementById('num_browsers').value = config.num_browsers || 10;
            document.getElementById('headless').checked = config.headless || false;
            document.getElementById('min_watch').value = config.min_watch_percentage || 0.7;
            document.getElementById('max_watch').value = config.max_watch_percentage || 1.0;
            document.getElementById('use_proxy').checked = config.use_proxy || false;
            document.getElementById('proxy_rotation').value = config.proxy_rotation || 'random';

        } catch (error) {
            console.error('Error loading configuration:', error);
            this.addStatusMessage('Error loading configuration', 'error');
        }
    }

    getConfiguration() {
        return {
            video_url: document.getElementById('video_url').value.trim(),
            num_browsers: parseInt(document.getElementById('num_browsers').value),
            headless: document.getElementById('headless').checked,
            min_watch_percentage: parseFloat(document.getElementById('min_watch').value),
            max_watch_percentage: parseFloat(document.getElementById('max_watch').value),
            use_proxy: document.getElementById('use_proxy').checked,
            proxy_rotation: document.getElementById('proxy_rotation').value
        };
    }

    async startWatchers() {
        const config = this.getConfiguration();

        // Validate
        if (!config.video_url) {
            this.addStatusMessage('Please enter a video URL', 'error');
            return;
        }

        if (config.num_browsers < 1 || config.num_browsers > 50) {
            this.addStatusMessage('Number of watchers must be between 1 and 50', 'error');
            return;
        }

        try {
            // Update UI
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
            this.isRunning = true;
            this.startTime = new Date();
            this.watchers = {};

            // Clear watchers grid
            document.getElementById('watchers-grid').innerHTML = '';

            // Start elapsed time counter
            this.startElapsedCounter();

            // Send start request
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();

            if (result.error) {
                this.addStatusMessage(result.error, 'error');
                this.resetUI();
            } else {
                this.addStatusMessage('Watchers starting...', 'info');
            }

        } catch (error) {
            console.error('Error starting watchers:', error);
            this.addStatusMessage('Error starting watchers: ' + error.message, 'error');
            this.resetUI();
        }
    }

    async stopWatchers() {
        try {
            const response = await fetch('/api/stop', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.error) {
                this.addStatusMessage(result.error, 'error');
            } else {
                this.addStatusMessage('Stopping all watchers...', 'info');
                this.resetUI();
            }

        } catch (error) {
            console.error('Error stopping watchers:', error);
            this.addStatusMessage('Error stopping watchers: ' + error.message, 'error');
        }
    }

    updateWatcher(data) {
        this.watchers[data.id] = data;

        // Check if watcher card exists
        let card = document.getElementById(`watcher-${data.id}`);

        if (!card) {
            // Create new watcher card
            card = this.createWatcherCard(data);
            const grid = document.getElementById('watchers-grid');

            // Remove empty state if present
            const emptyState = grid.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }

            grid.appendChild(card);
        } else {
            // Update existing card
            this.updateWatcherCard(card, data);
        }
    }

    createWatcherCard(data) {
        const card = document.createElement('div');
        card.className = 'watcher-card';
        card.id = `watcher-${data.id}`;

        card.innerHTML = `
            <div class="watcher-header">
                <div class="watcher-id">Watcher #${data.id}</div>
                <div class="watcher-status ${data.status}">${data.status}</div>
            </div>
            <div class="watcher-info">
                <div><strong>Strategy:</strong> ${data.strategy || 'N/A'}</div>
                <div><strong>Status:</strong> ${data.message}</div>
                <div><strong>Proxy:</strong> ${data.proxy || 'None'}</div>
            </div>
            <div class="watcher-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.progress || 0}%"></div>
                </div>
            </div>
        `;

        return card;
    }

    updateWatcherCard(card, data) {
        // Update status
        const statusEl = card.querySelector('.watcher-status');
        statusEl.className = `watcher-status ${data.status}`;
        statusEl.textContent = data.status;

        // Update message
        const messageEl = card.querySelector('.watcher-info div:nth-child(2)');
        messageEl.innerHTML = `<strong>Status:</strong> ${data.message}`;

        // Update progress
        const progressFill = card.querySelector('.progress-fill');
        progressFill.style.width = `${data.progress || 0}%`;
    }

    updateStatus(data) {
        // Update status cards
        document.getElementById('status-running').textContent = data.is_running ? 'Running' : 'Idle';
        document.getElementById('status-total').textContent = data.total_watchers || 0;
        document.getElementById('status-success').textContent = data.successful || 0;
        document.getElementById('status-failed').textContent = data.failed || 0;

        // If not running anymore, reset UI
        if (!data.is_running && this.isRunning) {
            this.resetUI();
        }
    }

    startElapsedCounter() {
        this.elapsedInterval = setInterval(() => {
            if (this.startTime) {
                const elapsed = Math.floor((new Date() - this.startTime) / 1000);
                document.getElementById('status-elapsed').textContent = this.formatTime(elapsed);
            }
        }, 1000);
    }

    stopElapsedCounter() {
        if (this.elapsedInterval) {
            clearInterval(this.elapsedInterval);
            this.elapsedInterval = null;
        }
    }

    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }

    resetUI() {
        this.isRunning = false;
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
        this.stopElapsedCounter();
    }

    addStatusMessage(message, type = 'info') {
        const messagesContainer = document.getElementById('status-messages');

        const messageEl = document.createElement('div');
        messageEl.className = `status-message ${type}`;

        const timestamp = new Date().toLocaleTimeString();
        messageEl.innerHTML = `<span>[${timestamp}]</span> <span>${message}</span>`;

        messagesContainer.appendChild(messageEl);

        // Auto-scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Keep only last 50 messages
        const messages = messagesContainer.querySelectorAll('.status-message');
        if (messages.length > 50) {
            messages[0].remove();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.watcherUI = new WatcherUI();
});
