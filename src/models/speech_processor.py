import speech_recognition as sr
import io
from pydub import AudioSegment
import numpy as np
import tempfile
import os

class SpeechProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def process_audio(self, audio_data):
        """Convert audio data to the format expected by speech recognition"""
        try:
            # Handle different audio formats (especially WebM from browsers)
            audio_segment = None
            
            # Try multiple format approaches for browser compatibility
            try:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            except:
                # If direct conversion fails, try with file extension hint
                try:
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
                except:
                    # Last resort: save to temp file and process
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                        temp_file.write(audio_data)
                        temp_file.flush()
                        audio_segment = AudioSegment.from_file(temp_file.name)
                        os.unlink(temp_file.name)
            
            if audio_segment is None:
                raise Exception("Could not process audio format")
            
            # Convert to WAV format with proper settings for speech recognition
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Export to bytes
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)
            
            return wav_io
        except Exception as e:
            raise Exception(f"Audio processing failed: {str(e)}")

    def transcribe_speech(self, audio_data):
        """Transcribe speech from processed audio data"""
        try:
            with sr.AudioFile(audio_data) as source:
                # Adjust for ambient noise with shorter duration for live processing
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.record(source)
            
            # Try Google first (most reliable for live transcription)
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
                return text.strip()
            except sr.UnknownValueError:
                return ""
            except sr.RequestError as e:
                print(f"Google Speech Recognition error: {e}")
                return ""
                    
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return ""

    def transcribe_live_chunk(self, audio_chunk):
        """Process a small chunk of audio for live transcription"""
        try:
            # Skip very small chunks that won't contain meaningful audio
            if len(audio_chunk) < 1024:  # Less than 1KB
                return ""
                
            processed_audio = self.process_audio(audio_chunk)
            return self.transcribe_speech(processed_audio)
        except Exception as e:
            print(f"Live chunk processing error: {str(e)}")
            return ""