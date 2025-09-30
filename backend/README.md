# ISL Sign Language Backend API

A Python backend API for converting speech and text to Indian Sign Language videos using FastAPI.

## Features

- **Speech-to-Sign**: Convert audio files to sign language videos
- **Text-to-Sign**: Convert text input to sign language videos  
- **Fast Video Generation**: Optimized video creation with adjustable speed
- **Google Speech-to-Text**: High-accuracy speech recognition
- **RESTful API**: Easy integration with web and mobile applications

## Setup Instructions

### Prerequisites

- Python 3.8+
- Google Cloud Account (for Speech-to-Text API)
- Sign language images folder

### Installation

1. **Clone and navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Linux/Mac
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google Cloud Speech-to-Text**:
   - Create a Google Cloud project
   - Enable Speech-to-Text API
   - Create service account and download JSON key
   - Set environment variable:
     ```bash
     set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\service-account-key.json
     ```

5. **Create output directory**:
   ```bash
   mkdir output_videos
   ```

### Running the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Access interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Speech-to-Sign Language
**POST** `/speech-to-sign`

Convert audio file to sign language video.

**Parameters:**
- `audio_file`: Audio file (wav, mp3, m4a, flac, ogg)
- `speed`: Video speed multiplier (default: 1.0)

**Response:**
```json
{
  "text": "extracted text",
  "video_path": "sign_video_20231201_143022_abc123.mp4",
  "message": "Successfully converted speech to sign language video"
}
```

### 2. Text-to-Sign Language
**POST** `/text-to-sign`

Convert text to sign language video.

**Request Body:**
```json
{
  "text": "hello world",
  "speed": 1.0
}
```

**Response:**
```json
{
  "text": "hello world",
  "video_path": "sign_video_20231201_143022_def456.mp4",
  "message": "Successfully converted text to sign language video"
}
```

### 3. Download Video
**GET** `/download-video/{video_filename}`

Download generated sign language video.

### 4. Health Check
**GET** `/health`

Check API health and service status.

### 5. Statistics
**GET** `/stats`

Get system statistics and loaded sign images.

## Usage Examples

### Using curl

**Text to Sign:**
```bash
curl -X POST "http://localhost:8000/text-to-sign" \
     -H "Content-Type: application/json" \
     -d '{"text": "hello world", "speed": 1.5}'
```

**Speech to Sign:**
```bash
curl -X POST "http://localhost:8000/speech-to-sign" \
     -F "audio_file=@audio.wav" \
     -F "speed=1.0"
```

**Download Video:**
```bash
curl -X GET "http://localhost:8000/download-video/sign_video_20231201_143022_abc123.mp4" \
     --output sign_video.mp4
```

### Using Python requests

```python
import requests

# Text to Sign
response = requests.post(
    "http://localhost:8000/text-to-sign",
    json={"text": "hello", "speed": 1.0}
)
result = response.json()
print(f"Video created: {result['video_path']}")

# Speech to Sign
with open("audio.wav", "rb") as f:
    files = {"audio_file": f}
    data = {"speed": 1.0}
    response = requests.post(
        "http://localhost:8000/speech-to-sign",
        files=files,
        data=data
    )
result = response.json()
print(f"Text extracted: {result['text']}")
print(f"Video created: {result['video_path']}")
```

## Configuration

### Video Settings
- **Frame Rate**: Automatically adjusted based on speed parameter
- **Resolution**: 480x640 pixels (optimized for mobile viewing)
- **Format**: MP4 with H.264 encoding
- **Duration**: ~1-2 seconds per character (adjustable with speed parameter)

### Supported Characters
- Numbers: 0-9
- Letters: a-z (uppercase and lowercase)
- Unsupported characters show placeholder frames

## Troubleshooting

### Common Issues

1. **Google Cloud Authentication Error**:
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set
   - Verify service account has Speech-to-Text API permissions

2. **Sign Images Not Found**:
   - Check that the path `../Code/Predict signs/Reverse sign images` exists
   - Verify image files (0.jpg, a.jpg, etc.) are present

3. **Video Generation Failed**:
   - Ensure OpenCV is properly installed
   - Check that output_videos directory exists and is writable

4. **Audio Processing Error**:
   - Install required audio codecs for pydub
   - Verify audio file format is supported

### Performance Tips

- Use lower speed values (0.5-0.8) for clearer sign language videos
- Higher speed values (1.5-2.0) for faster playback
- Shorter text inputs generate videos faster
- Use WAV format for best audio recognition accuracy

## Development

### Project Structure
```
backend/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── output_videos/      # Generated video files
```

### Adding New Features

To add support for new sign language gestures:
1. Add image files to the signs folder
2. Update the `char_mappings` dictionary in `TextToSignService._load_sign_images()`
3. Restart the server

## License

This project is part of the Indian Sign Language Recognition system.