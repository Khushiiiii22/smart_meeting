import json
import assemblyai as aai
import google.generativeai as genai
import config

# Configure APIs
genai.configure(api_key=config.GEMINI_API_KEY)
aai.settings.api_key = config.ASSEMBLYAI_API_KEY  # Your AssemblyAI API key in config.py


def transcribe_audio(local_file_path: str):
    """
    Transcribe a local audio file using AssemblyAI with speaker diarization enabled,
    returns both raw transcript text and structured dict to enable better formatting.
    """
    try:
        config = aai.TranscriptionConfig(speaker_labels=True, speakers_expected=2)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(local_file_path, config=config)

        print("Full transcript text:")
        print(transcript.text)

        # Build transcript_json dict
        transcript_json = {
            "text": transcript.text,
            "segments": []
        }

        # Use utterances if available (preferred)
        if hasattr(transcript, 'utterances') and transcript.utterances:
            print("Using utterances:")
            for utt in transcript.utterances:
                print(f"Speaker {utt.speaker}: {utt.text}")
                transcript_json["segments"].append({
                    "speaker": utt.speaker,
                    "start": getattr(utt, "start", 0),
                    "text": utt.text
                })
        # Fallback to segments if utterances not present
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
    if not json_response:
        return ""

    segments = json_response.get('segments')
    if not segments:
        # Return plain text with a note so user sees something, even if no diarization.
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




def generate_summary(transcript: str, prompt: str) -> str | None:
    """
    Use Gemini API to generate a summary or structured data based on a prompt and transcript.
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            {"role": "user", "parts": [f"{prompt}\n\n{transcript}"]}
        ])
        return response.text
    except Exception as e:
        print(f"[NLP] Summary generation failed: {e}")
        return None


def generate_minutes_of_meeting(transcript: str) -> dict | None:
    """
    Generate detailed minutes of meeting (MoM) JSON from the given transcript.
    Returns parsed JSON dictionary or None on failure.
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
