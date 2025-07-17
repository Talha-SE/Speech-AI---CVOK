from flask import Blueprint, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from models.speech_processor import SpeechProcessor
import logging
import base64

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
        if processed_audio:
            transcription = speech_processor.transcribe_speech(processed_audio)
            return jsonify({'transcription': transcription}), 200
        else:
            return jsonify({'error': 'Audio processing failed'}), 500
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
            logger.info(f"Received audio chunk")
            
            # Get audio data and handle different formats
            audio_data = data.get('audio')
            if not audio_data:
                logger.warning("No audio data in chunk")
                return
            
            # Convert audio data to bytes if it's a string (base64 encoded)
            if isinstance(audio_data, str):
                try:
                    # Decode base64 string to bytes
                    audio_bytes = base64.b64decode(audio_data)
                    logger.info(f"Decoded base64 audio data: {len(audio_bytes)} bytes")
                except Exception as e:
                    logger.error(f"Base64 decode error: {e}")
                    return
            else:
                # Already bytes
                audio_bytes = audio_data
                logger.info(f"Raw audio data: {len(audio_bytes)} bytes")
            
            # Process with VOSK
            transcription = speech_processor.transcribe_live_chunk(audio_bytes)
            
            if transcription and transcription.strip():
                logger.info(f"Sending transcription: '{transcription}'")
                emit('transcription', {'text': transcription})
            else:
                logger.info("No transcription result")
                
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected")
        emit('status', {'message': 'Connected to VOSK medium model transcription service'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected")
    
    return socketio