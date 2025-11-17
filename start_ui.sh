#!/bin/bash
# Quick start script for YouTube Watcher UI

echo "🎬 Starting YouTube Watcher UI..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if dependencies are installed
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if Playwright browsers are installed
if [ ! -d "$HOME/Library/Caches/ms-playwright" ] && [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "🌐 Installing Playwright browsers..."
    playwright install chromium
fi

echo ""
echo "✅ Starting Flask server..."
echo "📱 Open http://localhost:5000 in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the app
python app.py
