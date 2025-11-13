import os
from main import app, socketio

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=False,
        use_reloader=False,
        log_output=True
    )
