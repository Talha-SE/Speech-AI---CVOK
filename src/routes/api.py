from flask import Blueprint, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from models.speech_processor import SpeechProcessor
import base64

api = Blueprint('api', __name__)
speech_processor = SpeechProcessor()
socketio = None

@api.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files.get('audio')
    if not audio_file:
        return jsonify({'error': 'No audio file provided'}), 400

    try:
        audio_data = audio_file.read()
        processed_audio = speech_processor.process_audio(audio_data)
        transcription = speech_processor.transcribe_speech(processed_audio)
        return jsonify({'transcription': transcription}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/test')
def test_page():
    """Serve the live test page"""
    return render_template('test.html')

def setup_routes(app):
    app.register_blueprint(api)

def setup_socketio(app):
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @socketio.on('audio_chunk')
    def handle_audio_chunk(data):
        try:
            # Decode base64 audio data
            audio_data = base64.b64decode(data['audio'])
            transcription = speech_processor.transcribe_live_chunk(audio_data)
            
            if transcription.strip():  # Only emit if there's actual text
                emit('transcription', {'text': transcription})
        except Exception as e:
            emit('error', {'message': str(e)})
    
    @socketio.on('connect')
    def handle_connect():
        emit('status', {'message': 'Connected to live transcription service'})
    
    return socketio