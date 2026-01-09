#!/bin/bash
# Development entrypoint with file watcher for hot reload

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

if [ "$RELOAD_ENABLED" != "true" ]; then
    log "Hot reload DISABLED - Running app normally"
    exec python app.py
fi

log "🔥 Hot reload ENABLED - Watching for Python file changes..."

# Start app in background
python app.py &
APP_PID=$!

# Cleanup on exit
trap "kill $APP_PID 2>/dev/null || true" EXIT

# Watch for .py file changes (excluding tmp/ and data/)
while true; do
    # Check if app process is still running
    if ! kill -0 $APP_PID 2>/dev/null; then
        log "App process died, restarting..."
        python app.py &
        APP_PID=$!
    fi

    # Check for modified Python files
    if find . -type f -name "*.py" -not -path "./tmp/*" -not -path "./data/*" -newer /tmp/.reload_marker 2>/dev/null | grep -q .; then
        log "📝 Python files changed - restarting app..."
        kill $APP_PID 2>/dev/null || true
        wait $APP_PID 2>/dev/null || true
        sleep 1
        python app.py &
        APP_PID=$!
    fi

    touch /tmp/.reload_marker
    sleep 1
done
