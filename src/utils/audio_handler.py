from pydub import AudioSegment
import os

def save_audio(file, filename):
    file.save(filename)

def load_audio(filename):
    if os.path.exists(filename):
        audio = AudioSegment.from_file(filename)
        return audio
    else:
        raise FileNotFoundError(f"The file {filename} does not exist.")