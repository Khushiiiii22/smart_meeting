from dotenv import load_dotenv
import os
import json
import assemblyai as aai
from google.genai import Client
from typing import Optional

# Load environment variables from .env locally; Render reads from its own env store
load_dotenv()

# Read API keys
ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Fail fast if keys are missing
missing_vars = [var for var, val in {
    "ASSEMBLYAI_API_KEY": ASSEMBLYAI_API_KEY,
    "GEMINI_API_KEY": GEMINI_API_KEY
}.items() if not val]
if missing_vars:
    raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")

# Initialize SDKs
aai.settings.api_key = ASSEMBLYAI_API_KEY
client = Client(api_key=GEMINI_API_KEY)

def transcribe_audio(local_file_path: str):
    """
    Transcribe a local audio file using AssemblyAI with speaker diarization enabled,
    returns both raw transcript text and structured dict to enable better formatting.
    """
    try:
        config_ = aai.TranscriptionConfig(speaker_labels=True, speakers_expected=2)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(local_file_path, config=config_)

        print("Full transcript text:")
        print(transcript.text)

        # Build transcript JSON
        transcript_json = {
            "text": transcript.text,
            "segments": []
        }

        # Use utterances if available
        if hasattr(transcript, 'utterances') and transcript.utterances:
            print("Using utterances:")
            for utt in transcript.utterances:
                print(f"Speaker {utt.speaker}: {utt.text}")
                transcript_json["segments"].append({
                    "speaker": utt.speaker,
                    "start": getattr(utt, "start", 0),
                    "text": utt.text
                })
        # Fallback to segments
        elif hasattr(transcript, "segments") and transcript.segments:
            print("Using segments:")
            for seg in transcript.segments:
                print(f"Speaker {seg.speaker}: {seg.text}")
                transcript_json["segments"].append({
                    "speaker": seg.speaker,
                    "start": getattr(seg, "start", 0),
                    "text": seg.text
                })

        print("Final transcript_json:")
        print(json.dumps(transcript_json, indent=4))

        return transcript.text, transcript_json

    except Exception as e:
        print(f"[Transcription] Failed: {e}")
        return None, None


def format_transcript(json_response):
    """
    Format the JSON response from transcription into a human-readable string with timestamps and speakers.
    """
    if not json_response:
        return ""

    segments = json_response.get('segments')
    if not segments:
        return "(No speaker diarization data available)\n\n" + json_response.get('text', '')

    lines = []
    for seg in segments:
        speaker = seg.get('speaker', 'Speaker?')
        start = seg.get('start', 0) / 1000
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        text = seg.get('text', '').strip()
        lines.append(f"{timestamp} Speaker {speaker}: {text}")

    return "\n".join(lines)


def generate_summary(transcript: str, prompt: str) -> Optional[str]:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{prompt}\n\n{transcript}"
        )
        return response.text
    except Exception as e:
        print(f"[NLP] Summary generation failed: {e}")
        return None


def generate_minutes_of_meeting(transcript: str) -> Optional[dict]:
    """
    Generate detailed minutes of meeting (MoM) JSON from the given transcript.
    """
    prompt = (
        "Generate detailed Minutes of Meeting (MoM) from the following transcript. "
        "Return the result as a JSON object with the following fields:\n"
        "- title (string): Meeting title\n"
        "- date (string): Meeting date\n"
        "- time (string): Meeting time\n"
        "- attendees (list of strings): List of attendees\n"
        "- agenda (list of strings): Meeting agenda items\n"
        "- discussions (list of sections): Each section contains points or paragraphs\n"
        "- actions (list of strings): Action items and decisions\n"
        "- conclusion (string): Meeting conclusion\n"
        "- summary (string): Overall meeting summary\n\n"
        "Ensure the JSON is properly formatted and valid."
    )

    raw_response = generate_summary(transcript, prompt)
    if not raw_response:
        return None

    try:
        start = raw_response.find('{')
        end = raw_response.rfind('}') + 1
        json_str = raw_response[start:end]
        mom_data = json.loads(json_str)
        return mom_data
    except Exception as e:
        print(f"[NLP] Failed to parse MoM JSON: {e}")
        print("[NLP] Raw response:", raw_response)
        return None


if __name__ == "__main__":
    local_audio_path = "path/to/your/local/audiofile.mp3"

    print("Starting transcription with speaker diarization...")
    transcript_text, transcript_json = transcribe_audio(local_audio_path)

    if transcript_text:
        print("\nRaw transcript with speaker labels (plain text):")
        print(transcript_text)

        formatted_text = format_transcript(transcript_json)
        print("\nFormatted transcript:")
        print(formatted_text)

        print("\nGenerating minutes of meeting...")
        mom = generate_minutes_of_meeting(transcript_text)
        if mom:
            print("\nMinutes of Meeting JSON:")
            print(json.dumps(mom, indent=4))
        else:
            print("Failed to generate minutes of meeting.")
    else:
        print("Transcription failed.")
