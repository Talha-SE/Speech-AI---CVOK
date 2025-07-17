import io
from pydub import AudioSegment
import tempfile
import os
import logging
import json
import vosk
import requests
import zipfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechProcessor:
    def __init__(self):
        self.model = None
        self._setup_vosk_model()
        logger.info("SpeechProcessor initialized with VOSK medium English model")

    def _setup_vosk_model(self):
        """Setup VOSK medium English model (~128MB)"""
        try:
            model_path = "/tmp/vosk-model-medium"
            
            # Using medium model for better accuracy and reasonable size
            model_url = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip"
            
            if not os.path.exists(model_path):
                logger.info("Downloading VOSK medium English model (~128MB)...")
                
                response = requests.get(model_url, stream=True)
                model_zip_path = "/tmp/vosk-model-medium.zip"
                
                with open(model_zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info("Medium model downloaded, extracting...")
                
                with zipfile.ZipFile(model_zip_path, 'r') as zip_ref:
                    zip_ref.extractall("/tmp/")
                
                # The medium model extracts to this folder name
                extracted_folder = "/tmp/vosk-model-en-us-0.22-lgraph"
                if os.path.exists(extracted_folder):
                    os.rename(extracted_folder, model_path)
                    logger.info("VOSK medium English model (128MB) extracted successfully")
                
                os.remove(model_zip_path)
            else:
                logger.info("VOSK medium English model already exists")
            
            self.model = vosk.Model(model_path)
            logger.info("VOSK medium English model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup VOSK medium model: {e}")
            self.model = None

    def process_audio(self, audio_data):
        """Simple audio processing for VOSK"""
        try:
            logger.info(f"Processing audio data: {len(audio_data)} bytes")
            
            # Save audio data to temp file for pydub processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                temp_file_path = temp_file.name
            
            try:
                # Load and convert audio
                audio_segment = AudioSegment.from_file(temp_file_path)
                logger.info(f"Loaded audio: {audio_segment.frame_rate}Hz, {audio_segment.channels} channels")
                
                # Convert to VOSK format: 16000Hz, mono, 16-bit
                audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                
                # Get raw audio data
                raw_data = audio_segment.raw_data
                logger.info(f"Converted to VOSK format: {len(raw_data)} bytes")
                
                return raw_data
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            return None

    def transcribe_speech(self, audio_data):
        """Transcribe speech using VOSK medium model"""
        try:
            if not self.model or not audio_data:
                logger.error("VOSK medium model or audio data not available")
                return ""
            
            # Create recognizer
            rec = vosk.KaldiRecognizer(self.model, 16000)
            rec.SetWords(True)  # Enable word-level timestamps
            
            # Process all audio data at once
            if rec.AcceptWaveform(audio_data):
                result = json.loads(rec.Result())
                text = result.get('text', '')
                logger.info(f"VOSK medium model final result: '{text}'")
                return text.strip()
            else:
                # Get partial result
                partial_result = json.loads(rec.PartialResult())
                text = partial_result.get('partial', '')
                logger.info(f"VOSK medium model partial result: '{text}'")
                return text.strip()
                    
        except Exception as e:
            logger.error(f"VOSK medium model transcription error: {str(e)}")
            return ""

    def transcribe_live_chunk(self, audio_chunk):
        """Process audio chunk for live transcription using medium model"""
        try:
            if len(audio_chunk) < 10000:  # Skip very small chunks
                return ""
            
            logger.info(f"Processing live chunk with medium model: {len(audio_chunk)} bytes")
            processed_audio = self.process_audio(audio_chunk)
            
            if processed_audio:
                result = self.transcribe_speech(processed_audio)
                logger.info(f"Medium model live transcription: '{result}'")
                return result
            else:
                return ""
            
        except Exception as e:
            logger.error(f"Medium model live chunk error: {str(e)}")
            return ""