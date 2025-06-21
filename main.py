import eel
import threading
from main_app import app

# Start Flask in background
def run_flask():
    app.run(host='127.0.0.1', port=5001, debug=False)

# Start Eel - serves a dummy HTML to track browser tab
eel.init('web')  # put an empty index.html here or actual UI

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    eel.start('index.html', mode='chrome', block=True, close_callback=lambda route, websockets: exit(0))