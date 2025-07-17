from flask import Blueprint, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from models.speech_processor import SpeechProcessor
import base64
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    
    @socketio.on('audio_chunk')
    def handle_audio_chunk(data):
        try:
            logger.info(f"Received audio chunk of size: {len(data.get('audio', ''))}")
            
            # Decode base64 audio data
            audio_data = base64.b64decode(data['audio'])
            logger.info(f"Decoded audio data size: {len(audio_data)} bytes")
            
            if len(audio_data) < 1000:  # Skip very small chunks
                logger.info("Skipping small audio chunk")
                return
            
            transcription = speech_processor.transcribe_live_chunk(audio_data)
            logger.info(f"Transcription result: '{transcription}'")
            
            if transcription and transcription.strip():  # Only emit if there's actual text
                emit('transcription', {'text': transcription})
                logger.info(f"Emitted transcription: {transcription}")
            else:
                logger.info("No transcription text to emit")
                
        except Exception as e:
            logger.error(f"Error processing audio chunk: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected to WebSocket")
        emit('status', {'message': 'Connected to live transcription service'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected from WebSocket")
    
    return socketio