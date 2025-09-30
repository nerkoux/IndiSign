from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import logging
import uuid
from datetime import datetime
import cv2
import numpy as np
from pydub import AudioSegment
import speech_recognition as sr

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ISL Sign Language Dashboard", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
SIGNS_FOLDER = "../Code/Predict signs/Reverse sign images"
OUTPUT_FOLDER = "output_videos"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global sign images storage
sign_images = {}

def load_sign_images():
    """Load all sign language images into memory"""
    global sign_images
    signs_path = os.path.abspath(SIGNS_FOLDER)
    mappings = {c: f"{c}.jpg" for c in list("abcdefghijklmnopqrstuvwxyz0123456789")}
    for char, filename in mappings.items():
        image_path = os.path.join(signs_path, filename)
        if os.path.exists(image_path):
            img = cv2.imread(image_path)
            if img is not None:
                sign_images[char] = cv2.resize(img, (480, 640))
    logger.info(f"Loaded {len(sign_images)} sign images")

def speech_to_text(audio_file_path: str) -> str:
    """Convert audio to text using Google Speech Recognition"""
    recognizer = sr.Recognizer()

    # Always re-encode input to WAV PCM
    wav_path = audio_file_path + "_fixed.wav"
    audio = AudioSegment.from_file(audio_file_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(wav_path, format="wav")

    with sr.AudioFile(wav_path) as source:
        recognizer.adjust_for_ambient_noise(source)
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
        return text.lower().strip()
    except sr.UnknownValueError:
        raise ValueError("Could not understand audio")
    except sr.RequestError as e:
        raise ValueError(f"Google Speech Recognition error: {e}")
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)

def create_sign_video(text: str) -> str:
    """Create sign language video from text with web-compatible codec"""
    if not sign_images:
        raise ValueError("Sign images not loaded")

    clean_text = ''.join(c for c in text.lower() if c.isalnum() or c.isspace())
    if not clean_text.strip():
        raise ValueError("No valid characters in text")

    fps = 15  # Increased from 10 to 15 for faster playback
    char_frames = 6  # Reduced from 10 to 6 frames per character
    space_frames = 3  # Reduced from 5 to 3 frames for spaces

    first_img = next(iter(sign_images.values()))
    h, w = first_img.shape[:2]

    filename = f"sign_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.mp4"
    path = os.path.join(OUTPUT_FOLDER, filename)

    # Try H.264 codecs in order of preference for web compatibility
    codecs_to_try = [
        ('avc1', cv2.VideoWriter_fourcc(*'avc1')),  # H.264 - best for web
        ('H264', cv2.VideoWriter_fourcc(*'H264')),  # H.264 alternative
        ('X264', cv2.VideoWriter_fourcc(*'X264')),  # H.264 alternative
        ('mp4v', cv2.VideoWriter_fourcc(*'mp4v')),  # Fallback
    ]
    
    writer = None
    for codec_name, fourcc in codecs_to_try:
        writer = cv2.VideoWriter(path, fourcc, fps, (w, h))
        if writer.isOpened():
            logger.info(f"Using codec: {codec_name}")
            break
        writer.release()
    
    if writer is None or not writer.isOpened():
        raise ValueError("Could not create video file with any codec")

    try:
        fade_frames = 2  # Reduced from 3 to 2 frames for quicker transitions
        
        for i, c in enumerate(clean_text):
            if c == " ":
                black = np.zeros((h, w, 3), dtype=np.uint8)
                for _ in range(space_frames):
                    writer.write(black)
            elif c in sign_images:
                frame = sign_images[c].copy()
                label = f"'{c.upper()}'"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
                tx = (w - tw) // 2
                ty = h - 40
                cv2.putText(frame, label, (tx+2, ty+2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,0), 4)
                cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 3)
                
                # Fade in transition at the start
                for fade_idx in range(fade_frames):
                    alpha = fade_idx / fade_frames
                    black = np.zeros((h, w, 3), dtype=np.uint8)
                    faded_frame = cv2.addWeighted(black, 1 - alpha, frame, alpha, 0)
                    writer.write(faded_frame)
                
                # Hold frame
                for _ in range(char_frames - 2 * fade_frames):
                    writer.write(frame)
                
                # Fade out transition at the end (except for last character)
                if i < len(clean_text) - 1:
                    for fade_idx in range(fade_frames):
                        alpha = (fade_frames - fade_idx) / fade_frames
                        black = np.zeros((h, w, 3), dtype=np.uint8)
                        faded_frame = cv2.addWeighted(black, 1 - alpha, frame, alpha, 0)
                        writer.write(faded_frame)
                else:
                    # For last character, just hold the frame
                    for _ in range(fade_frames):
                        writer.write(frame)
    finally:
        writer.release()

    logger.info(f"Created video {filename} for '{text}'")
    return filename

# Load on startup
load_sign_images()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Main dashboard to test both APIs"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISL Sign Language Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { 
            max-width: 800px; margin: 0 auto; background: white; 
            border-radius: 20px; padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        }
        h1 { 
            text-align: center; color: #333; margin-bottom: 40px; font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .section { 
            margin-bottom: 40px; padding: 30px; 
            border: 2px solid #e1e8ed; border-radius: 15px; 
            background: linear-gradient(145deg, #f8f9fa, #ffffff);
        }
        .section h2 { color: #495057; margin-bottom: 20px; font-size: 1.5em; }
        textarea { 
            width: 100%; padding: 15px; border: 2px solid #dee2e6; 
            border-radius: 10px; font-size: 16px; resize: vertical; font-family: inherit;
        }
        button { 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; border: none; padding: 15px 30px; 
            border-radius: 10px; font-size: 16px; font-weight: bold;
            cursor: pointer; margin-top: 15px; transition: all 0.3s ease;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3); }
        button:disabled { background: #6c757d; cursor: not-allowed; transform: none; }
        .recording { background: linear-gradient(135deg, #dc3545, #c82333) !important; }
        .status { 
            margin: 15px 0; padding: 10px; border-radius: 8px; font-weight: bold;
        }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .video-container { text-align: center; margin: 20px 0; }
        video { 
            max-width: 100%; height: auto; border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); background: #000;
        }
        .video-info { margin-top: 10px; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤟 ISL Sign Language Dashboard</h1>
        
        <!-- Text to Sign Section -->
        <div class="section">
            <h2>📝 Text to Sign Language</h2>
            <textarea id="textInput" rows="4" placeholder="Type your message here (e.g., hello world)..."></textarea>
            <button onclick="convertText()">Convert Text to Sign Video</button>
            <div id="textResult"></div>
        </div>
        
        <!-- Speech to Sign Section -->
        <div class="section">
            <h2>🎤 Speech to Sign Language</h2>
            <button id="recordBtn" onclick="toggleRecording()">🎤 Start Recording</button>
            <div id="speechStatus"></div>
            <div id="speechResult"></div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;

        // Text to Sign Conversion
        async function convertText() {
            const text = document.getElementById('textInput').value.trim();
            const resultDiv = document.getElementById('textResult');
            
            if (!text) {
                resultDiv.innerHTML = '<div class="status error">Please enter some text</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div class="status info">Creating sign language video...</div>';
            
            try {
                const response = await fetch(`${API_BASE}/text-to-sign`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showVideo(resultDiv, data.video_file, `Text: "${data.text}"`);
                } else {
                    resultDiv.innerHTML = `<div class="status error">Error: ${data.detail}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="status error">Error: ${error.message}</div>`;
            }
        }

        // Speech Recording
        async function toggleRecording() {
            const btn = document.getElementById('recordBtn');
            const statusDiv = document.getElementById('speechStatus');
            
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = event => {
                        if (event.data.size > 0) audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        convertSpeech(audioBlob);
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    btn.textContent = '🛑 Stop Recording';
                    btn.className = 'recording';
                    statusDiv.innerHTML = '<div class="status info">🔴 Recording... Click stop when done</div>';
                    
                } catch (error) {
                    statusDiv.innerHTML = '<div class="status error">Microphone access denied. Please allow microphone access.</div>';
                }
            } else {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                isRecording = false;
                btn.textContent = '🎤 Start Recording';
                btn.className = '';
                statusDiv.innerHTML = '<div class="status info">Processing audio...</div>';
            }
        }

        // Speech to Sign Conversion
        async function convertSpeech(audioBlob) {
            const statusDiv = document.getElementById('speechStatus');
            const resultDiv = document.getElementById('speechResult');
            
            try {
                const formData = new FormData();
                formData.append('audio_file', audioBlob, 'recording.webm');
                
                statusDiv.innerHTML = '<div class="status info">Converting speech to text...</div>';
                
                const response = await fetch(`${API_BASE}/speech-to-sign`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                statusDiv.innerHTML = '';
                
                if (response.ok) {
                    showVideo(resultDiv, data.video_file, `Speech: "${data.text}"`);
                } else {
                    resultDiv.innerHTML = `<div class="status error">Error: ${data.detail}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = '';
                resultDiv.innerHTML = `<div class="status error">Error: ${error.message}</div>`;
            }
        }

        // Show Video with better error handling
        function showVideo(div, videoFile, caption) {
            const videoUrl = `${API_BASE}/video/${videoFile}`;
            const timestamp = new Date().getTime();
            div.innerHTML = `
                <div class="status success">✅ Video created successfully!</div>
                <div class="video-container">
                    <video controls autoplay muted preload="auto" style="width: 100%; max-width: 640px;">
                        <source src="${videoUrl}?t=${timestamp}" type="video/mp4">
                        Your browser does not support video playback.
                    </video>
                    <div class="video-info">${caption}</div>
                </div>
            `;
            
            // Add error handling for video loading
            const videoElement = div.querySelector('video');
            videoElement.addEventListener('error', function(e) {
                console.error('Video error:', e);
                div.innerHTML += '<div class="status error">Video playback error. File may not be compatible with your browser.</div>';
            });
            
            videoElement.addEventListener('loadeddata', function() {
                console.log('Video loaded successfully');
            });
        }
    </script>
</body>
</html>
    """)

@app.post("/text-to-sign")
def text_to_sign(data: dict = Body(...)):
    text = data.get("text", "").strip()
    if not text:
        raise HTTPException(400, "Text is required")
    try:
        file = create_sign_video(text)
        return {"video_file": file, "text": text}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/speech-to-sign")
def speech_to_sign(audio_file: UploadFile = File(...)):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            tmp.write(audio_file.file.read())
            tmp_path = tmp.name
        text = speech_to_text(tmp_path)
        if not text:
            raise ValueError("No speech detected")
        file = create_sign_video(text)
        return {"video_file": file, "text": text}
    except Exception as e:
        logger.error(f"Speech error: {e}")
        raise HTTPException(500, str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.get("/video/{video_filename}")
def get_video(video_filename: str):
    path = os.path.join(OUTPUT_FOLDER, video_filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Video not found")
    return FileResponse(
        path, 
        media_type="video/mp4", 
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)