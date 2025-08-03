import requests
import time
import config


ASSEMBLYAI_API_KEY = config.ASSEMBLYAI_API_KEY
UPLOAD_ENDPOINT = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_ENDPOINT = "https://api.assemblyai.com/v2/transcript"
HEADERS = {"authorization": ASSEMBLYAI_API_KEY}


def upload_file_to_assemblyai(file_path: str) -> str:
    """
    Uploads audio/video file to AssemblyAI and returns an upload URL.
    """
    with open(file_path, 'rb') as f:
        response = requests.post(UPLOAD_ENDPOINT, headers=HEADERS, data=f)
    response.raise_for_status()
    upload_url = response.json().get('upload_url')
    if not upload_url:
        raise ValueError("No upload_url returned by AssemblyAI")
    return upload_url


def request_transcript(upload_url: str) -> str:
    """
    Requests transcription job with speaker diarization enabled.
    Returns the transcript ID.
    """
    payload = {
        "audio_url": upload_url,
        "speaker_labels": True,  # enables speaker diarization
        "auto_chapters": False  # optional: disable chapters for simpler output
    }
    response = requests.post(TRANSCRIPT_ENDPOINT, json=payload, headers=HEADERS)
    response.raise_for_status()
    transcript_id = response.json().get('id')
    if not transcript_id:
        raise ValueError("Transcript ID not returned from AssemblyAI")
    return transcript_id


def poll_transcription(transcript_id: str, poll_interval: int = 10, timeout: int = 600) -> dict | None:
    """
    Poll transcription status every poll_interval seconds until complete or failed.
    Returns the full JSON response on success, None on failure or timeout.
    """
    elapsed = 0
    while elapsed < timeout:
        response = requests.get(f"{TRANSCRIPT_ENDPOINT}/{transcript_id}", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        status = data.get('status')
        if status == 'completed':
            return data
        elif status == 'failed':
            print(f"Transcription failed: {data.get('error')}")
            return None
        else:
            print(f"Transcription status: {status}. Waiting {poll_interval}s...")
        time.sleep(poll_interval)
        elapsed += poll_interval
    print("Transcription polling timed out.")
    return None


def format_transcript_with_speakers(transcript_json: dict) -> str:
    """
    Formats AssemblyAI transcript JSON into a multi-line string with speaker labels and timestamps.
    """
    if not transcript_json:
        return ""

    segments = transcript_json.get('segments')
    if not segments:
        # fallback to plain text if segments are missing
        return transcript_json.get('text', '')

    lines = []
    for seg in segments:
        speaker = seg.get('speaker', 'Unknown')
        start_ms = seg.get('start', 0)
        start_sec = start_ms / 1000
        minutes = int(start_sec // 60)
        seconds = int(start_sec % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        text = seg.get('text', '').strip()
        lines.append(f"{timestamp} Speaker {speaker}: {text}")

    return "\n".join(lines)


def get_transcript(file_path: str) -> str | None:
    """
    High-level function to get speaker-labeled transcription text from a local audio file.
    Returns formatted transcript string or None on failure.
    """
    try:
        print("Uploading file to AssemblyAI...")
        upload_url = upload_file_to_assemblyai(file_path)

        print("Requesting transcription with speaker diarization...")
        transcript_id = request_transcript(upload_url)

        print("Polling for transcription completion...")
        transcript_json = poll_transcription(transcript_id)

        if not transcript_json:
            print("Failed to get transcription result.")
            return None

        print("Formatting transcription with speaker labels...")
        formatted_text = format_transcript_with_speakers(transcript_json)
        return formatted_text

    except Exception as e:
        print(f"Error in get_transcript: {e}")
        return None
