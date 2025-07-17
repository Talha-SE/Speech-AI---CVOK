import io
from pydub import AudioSegment
import numpy as np
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
        logger.info("SpeechProcessor initialized with VOSK small English model")

    def _setup_vosk_model(self):
        """Setup VOSK small English model for speech recognition"""
        try:
            model_path = "/tmp/vosk-model-small"
            # Using the smallest English model for faster deployment
            model_url = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip"
            
            # Check if model already exists
            if not os.path.exists(model_path):
                logger.info("Downloading VOSK small English model...")
                
                # Download model
                response = requests.get(model_url, stream=True)
                model_zip_path = "/tmp/vosk-model-small.zip"
                
                with open(model_zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info("Model downloaded, extracting...")
                
                # Extract model
                with zipfile.ZipFile(model_zip_path, 'r') as zip_ref:
                    zip_ref.extractall("/tmp/")
                
                # Rename extracted folder to standard name
                extracted_folder = "/tmp/vosk-model-en-us-0.22-lgraph"
                if os.path.exists(extracted_folder):
                    os.rename(extracted_folder, model_path)
                    logger.info("VOSK small English model extracted successfully")
                
                # Clean up
                os.remove(model_zip_path)
            else:
                logger.info("VOSK small English model already exists")
            
            # Initialize VOSK model
            self.model = vosk.Model(model_path)
            logger.info("VOSK small English model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup VOSK small model: {e}")
            self.model = None

    def process_audio(self, audio_data):
        """Convert audio data to the format expected by VOSK"""
        try:
            logger.info(f"Processing audio data of size: {len(audio_data)} bytes")
            
            # Try to create audio segment from raw data first
            try:
                audio_segment = AudioSegment(
                    data=audio_data,
                    sample_width=2,  # 16-bit
                    frame_rate=48000,  # Browser default
                    channels=1
                )
                logger.info("Created audio segment from raw PCM data")
            except Exception as raw_error:
                logger.warning(f"Raw PCM failed: {raw_error}")
                
                # Fallback: try to decode as WebM
                temp_file_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                        temp_file.write(audio_data)
                        temp_file.flush()
                        temp_file_path = temp_file.name
                    
                    audio_segment = AudioSegment.from_file(temp_file_path, format="webm")
                    logger.info("Successfully loaded audio as WebM")
                    
                except Exception as webm_error:
                    logger.error(f"WebM processing failed: {webm_error}")
                    raise Exception(f"Could not process audio format: {webm_error}")
                finally:
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
            
            # Convert to VOSK required format: 16000Hz, mono, 16-bit
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Get raw audio data for VOSK
            raw_data = audio_segment.raw_data
            
            logger.info(f"Processed audio for VOSK: 16000Hz, 1 channel, {len(raw_data)} bytes")
            return raw_data
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise Exception(f"Audio processing failed: {str(e)}")

    def transcribe_speech(self, audio_data):
        """Transcribe speech using VOSK small English model only"""
        try:
            if not self.model:
                logger.error("VOSK small model not available")
                return ""
            
            # Create recognizer for this audio chunk
            rec = vosk.KaldiRecognizer(self.model, 16000)
            
            # Process audio data with VOSK
            if rec.AcceptWaveform(audio_data):
                result = json.loads(rec.Result())
                text = result.get('text', '')
                logger.info(f"VOSK small model transcription: '{text}'")
                return text.strip()
            else:
                # Get partial result for live processing
                partial_result = json.loads(rec.PartialResult())
                text = partial_result.get('partial', '')
                if text:
                    logger.info(f"VOSK small model partial: '{text}'")
                    return text.strip()
                else:
                    return ""
                    
        except Exception as e:
            logger.error(f"VOSK small model transcription error: {str(e)}")
            return ""

    def transcribe_live_chunk(self, audio_chunk):
        """Process audio chunk for live transcription using VOSK small model only"""
        try:
            # Skip small chunks
            if len(audio_chunk) < 8000:
                logger.info(f"Skipping small audio chunk: {len(audio_chunk)} bytes")
                return ""
            
            logger.info(f"Processing live chunk with VOSK small model: {len(audio_chunk)} bytes")
            processed_audio = self.process_audio(audio_chunk)
            result = self.transcribe_speech(processed_audio)
            logger.info(f"VOSK small model live result: '{result}'")
            return result
            
        except Exception as e:
            logger.error(f"Live chunk processing error: {str(e)}")
            return ""