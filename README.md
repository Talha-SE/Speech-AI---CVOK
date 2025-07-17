# Speech to Text API

This project is a simple Speech to Text API built using Flask. It allows users to convert audio speech into text through a RESTful API.

## Project Structure

```
speech-to-text-api
├── src
│   ├── app.py               # Entry point of the application
│   ├── models
│   │   └── speech_processor.py # Contains the SpeechProcessor class for audio processing
│   ├── routes
│   │   └── api.py           # Defines the API endpoints
│   └── utils
│       └── audio_handler.py  # Utility functions for handling audio files
├── requirements.txt          # Lists the project dependencies
├── Dockerfile                 # Docker configuration for the application
├── render.yaml                # Deployment configuration for Render.com
└── README.md                  # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd speech-to-text-api
   ```

2. **Install dependencies:**
   It is recommended to create a virtual environment before installing the dependencies.
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```
   python src/app.py
   ```

   The API will be available at `http://localhost:5000`.

## API Usage

### Transcribe Audio

- **Endpoint:** `POST /transcribe`
- **Description:** Accepts audio data and returns the transcribed text.
- **Request Body:** The audio file should be sent as form-data with the key `file`.

### Example Request

```bash
curl -X POST http://localhost:5000/transcribe -F "file=@path_to_audio_file.wav"
```

### Example Response

```json
{
  "transcription": "This is the transcribed text from the audio."
}
```

## Deployment

To deploy the application on Render.com, ensure you have the `render.yaml` file configured correctly. Follow the instructions on Render's documentation to set up your service.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.