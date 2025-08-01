import json
import google.generativeai as genai
import config

genai.configure(api_key=config.GEMINI_API_KEY)

def generate_summary(transcript, prompt):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            {"role": "user", "parts": [f"{prompt}\n\n{transcript}"]}
        ])
        return response.text
    except Exception as e:
        print(f"[NLP] Summary generation failed: {e}")
        return None


def generate_minutes_of_meeting(transcript):
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

    # Try to parse the JSON from the response text
    try:
        # Sometimes LLM responses contain explanatory text before/after JSON,
        # try to extract JSON substring:
        start = raw_response.find('{')
        end = raw_response.rfind('}') + 1
        json_str = raw_response[start:end]
        mom_data = json.loads(json_str)
        return mom_data
    except Exception as e:
        print(f"[NLP] Failed to parse MoM JSON: {e}")
        print("[NLP] Raw response:", raw_response)
        # If parsing fails, you can return raw text or None based on your app logic
        return None
