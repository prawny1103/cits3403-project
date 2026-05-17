from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # We use the socketio run function to support websockets
    socketio.run(app, debug=True)