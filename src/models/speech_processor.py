import speech_recognition as sr
import io
from pydub import AudioSegment
import numpy as np
import tempfile
import os
import logging
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        logger.info("SpeechProcessor initialized")

    def process_audio(self, audio_data):
        """Convert audio data to the format expected by speech recognition"""
        try:
            logger.info(f"Processing audio data of size: {len(audio_data)} bytes")
            
            # Handle different audio formats (especially WebM from browsers)
            audio_segment = None
            temp_file_path = None
            
            try:
                # First, try to process as raw WebM data using temp file approach
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                    temp_file.write(audio_data)
                    temp_file.flush()
                    temp_file_path = temp_file.name
                
                # Try to load the WebM file
                try:
                    audio_segment = AudioSegment.from_file(temp_file_path, format="webm")
                    logger.info("Successfully loaded audio as WebM from temp file")
                except Exception as webm_error:
                    logger.warning(f"WebM temp file failed: {webm_error}")
                    
                    # Try as raw audio data
                    try:
                        # Create a basic WAV header and append the audio data
                        # This is a fallback for cases where WebM decoding fails
                        sample_rate = 16000
                        channels = 1
                        bits_per_sample = 16
                        
                        # Create minimal WAV with the audio data
                        audio_segment = AudioSegment(
                            data=audio_data,
                            sample_width=2,  # 16-bit
                            frame_rate=sample_rate,
                            channels=channels
                        )
                        logger.info("Created audio segment from raw data")
                    except Exception as raw_error:
                        logger.error(f"Raw audio processing failed: {raw_error}")
                        raise Exception(f"Could not process audio format: {raw_error}")
                        
            finally:
                # Clean up temp file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
            
            if audio_segment is None:
                raise Exception("Could not process audio format")
            
            # Log audio properties
            try:
                logger.info(f"Original audio: {audio_segment.frame_rate}Hz, {audio_segment.channels} channels, {len(audio_segment)}ms duration")
            except:
                logger.info("Audio properties could not be logged")
            
            # Convert to WAV format with proper settings for speech recognition
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Export to bytes
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)
            
            logger.info(f"Processed audio: 16000Hz, 1 channel, WAV format, size: {wav_io.getbuffer().nbytes} bytes")
            return wav_io
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise Exception(f"Audio processing failed: {str(e)}")

    def transcribe_speech(self, audio_data):
        """Transcribe speech from processed audio data"""
        try:
            with sr.AudioFile(audio_data) as source:
                # Adjust for ambient noise with shorter duration for live processing
                self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                audio = self.recognizer.record(source)
                logger.info(f"Audio recorded from file source, duration: {len(audio.frame_data)} bytes")
            
            # Try Google first (most reliable for live transcription)
            try:
                logger.info("Attempting Google Speech Recognition...")
                text = self.recognizer.recognize_google(audio, language='en-US')
                logger.info(f"Google recognition successful: '{text}'")
                return text.strip()
            except sr.UnknownValueError:
                logger.warning("Google Speech Recognition could not understand audio")
                return ""
            except sr.RequestError as e:
                logger.error(f"Google Speech Recognition error: {e}")
                return ""
                    
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return ""

    def transcribe_live_chunk(self, audio_chunk):
        """Process a small chunk of audio for live transcription"""
        try:
            # Skip very small chunks that won't contain meaningful audio
            if len(audio_chunk) < 8000:  # Increased threshold to 8KB
                logger.info(f"Skipping small audio chunk: {len(audio_chunk)} bytes")
                return ""
            
            logger.info(f"Processing live chunk: {len(audio_chunk)} bytes")
            processed_audio = self.process_audio(audio_chunk)
            result = self.transcribe_speech(processed_audio)
            logger.info(f"Live transcription result: '{result}'")
            return result
            
        except Exception as e:
            logger.error(f"Live chunk processing error: {str(e)}")
            return ""