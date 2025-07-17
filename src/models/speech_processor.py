import speech_recognition as sr
import io
from pydub import AudioSegment
import numpy as np
import tempfile
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        logger.info("SpeechProcessor initialized")

    def process_audio(self, audio_data):
        """Convert audio data to the format expected by speech recognition"""
        try:
            logger.info(f"Processing audio data of size: {len(audio_data)} bytes")
            
            # Handle different audio formats (especially WebM from browsers)
            audio_segment = None
            
            # Try multiple format approaches for browser compatibility
            try:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
                logger.info("Successfully loaded audio with default format detection")
            except Exception as e1:
                logger.warning(f"Default format failed: {e1}")
                # If direct conversion fails, try with file extension hint
                try:
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
                    logger.info("Successfully loaded audio as WebM")
                except Exception as e2:
                    logger.warning(f"WebM format failed: {e2}")
                    # Last resort: save to temp file and process
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                            temp_file.write(audio_data)
                            temp_file.flush()
                            audio_segment = AudioSegment.from_file(temp_file.name)
                            os.unlink(temp_file.name)
                            logger.info("Successfully loaded audio via temp file")
                    except Exception as e3:
                        logger.error(f"All audio format attempts failed: {e3}")
                        raise Exception(f"Could not process audio format: {e3}")
            
            if audio_segment is None:
                raise Exception("Could not process audio format")
            
            # Log audio properties
            logger.info(f"Original audio: {audio_segment.frame_rate}Hz, {audio_segment.channels} channels, {len(audio_segment)}ms duration")
            
            # Convert to WAV format with proper settings for speech recognition
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Export to bytes
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)
            
            logger.info(f"Processed audio: 16000Hz, 1 channel, WAV format")
            return wav_io
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise Exception(f"Audio processing failed: {str(e)}")

    def transcribe_speech(self, audio_data):
        """Transcribe speech from processed audio data"""
        try:
            with sr.AudioFile(audio_data) as source:
                # Adjust for ambient noise with shorter duration for live processing
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.record(source)
                logger.info("Audio recorded from file source")
            
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
            if len(audio_chunk) < 5000:  # Increased threshold to 5KB
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