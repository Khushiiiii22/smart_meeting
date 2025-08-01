import requests
import time
import config

ASSEMBLYAI_API_KEY = config.ASSEMBLYAI_API_KEY
UPLOAD_ENDPOINT = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_ENDPOINT = "https://api.assemblyai.com/v2/transcript"
HEADERS = {"authorization": ASSEMBLYAI_API_KEY}


def upload_file_to_assemblyai(file_path):
    """Uploads audio/video file and returns an upload URL."""
    with open(file_path, 'rb') as f:
        response = requests.post(UPLOAD_ENDPOINT, headers=HEADERS, data=f)
    response.raise_for_status()
    upload_url = response.json().get('upload_url')
    if not upload_url:
        raise ValueError("No upload_url returned by AssemblyAI")
    return upload_url


def request_transcript(upload_url):
    """Requests transcription job and returns transcript ID."""
    payload = {
        "audio_url": upload_url,
        "speaker_labels": True  # Optional: enables speaker diarization
    }
    response = requests.post(TRANSCRIPT_ENDPOINT, json=payload, headers=HEADERS)
    response.raise_for_status()
    transcript_id = response.json().get('id')
    if not transcript_id:
        raise ValueError("Transcript ID not returned")
    return transcript_id


def poll_transcription(transcript_id, poll_interval=10, timeout=600):
    """Polls transcription status until completed or timeout."""
    elapsed = 0
    while elapsed < timeout:
        response = requests.get(f"{TRANSCRIPT_ENDPOINT}/{transcript_id}", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        status = data.get('status')
        if status == 'completed':
            return data.get('text')
        elif status == 'failed':
            print(f"Transcription failed: {data.get('error')}")
            return None
        else:
            print(f"Transcription status: {status}. Waiting {poll_interval}s...")
        time.sleep(poll_interval)
        elapsed += poll_interval
    print("Transcription polling timed out.")
    return None


def get_transcript(file_path):
    """High-level function: upload and get transcription text."""
    try:
        upload_url = upload_file_to_assemblyai(file_path)
        transcript_id = request_transcript(upload_url)
        transcription_text = poll_transcription(transcript_id)
        return transcription_text
    except Exception as e:
        print(f"Error in get_transcript: {e}")
        return None
