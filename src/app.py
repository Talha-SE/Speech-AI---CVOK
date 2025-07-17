from flask import Flask
from routes.api import setup_routes, setup_socketio
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

    # Create templates directory if it doesn't exist
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)

    app.template_folder = template_dir

    @app.route('/')
    def home():
        return "Welcome to the Live Speech to Text API! Visit /test for live testing."

    setup_routes(app)
    socketio = setup_socketio(app)
    return app, socketio

# For gunicorn deployment
app, socketio = create_app()

if __name__ == '__main__':
    # For local development
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)