import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

# --------------------------------------------------
# Load environment variables from .env (local only)
# --------------------------------------------------
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

# Initialize Supabase client once
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_meeting(meeting_data: dict):
    """Insert a new meeting record."""
    try:
        response = supabase.table("meetings").insert(meeting_data).execute()
        if hasattr(response, 'error') and response.error:
            print("Error adding meeting:", response.error)
            return None
        return response.data
    except Exception as e:
        print("Exception adding meeting:", e)
        return None

def add_meeting_attendee(attendee_data: dict):
    """Insert a meeting attendee record."""
    try:
        response = supabase.table("meeting_attendees").insert(attendee_data).execute()
        if hasattr(response, 'error') and response.error:
            print("Error adding attendee:", response.error)
            return None
        return response.data
    except Exception as e:
        print("Exception adding attendee:", e)
        return None

def add_meeting_minute(minute_data: dict):
    """Insert meeting minute record."""
    try:
        response = supabase.table("meeting_minutes").insert(minute_data).execute()
        if hasattr(response, 'error') and response.error:
            print("Error adding meeting minute:", response.error)
            return None
        return response.data
    except Exception as e:
        print("Exception adding meeting minute:", e)
        return None

def get_meetings():
    """Fetch all meetings."""
    try:
        response = supabase.table("meetings").select("*").execute()
        if hasattr(response, 'error') and response.error:
            print("Error fetching meetings:", response.error)
            return None
        return response.data
    except Exception as e:
        print("Exception fetching meetings:", e)
        return None

def get_meeting_attendees(meeting_id):
    """Fetch attendees for a given meeting ID."""
    try:
        response = supabase.table("meeting_attendees").select("*").eq("meeting_id", meeting_id).execute()
        if hasattr(response, 'error') and response.error:
            print("Error fetching attendees:", response.error)
            return None
        return response.data
    except Exception as e:
        print("Exception fetching attendees:", e)
        return None

def get_meeting_minutes(meeting_id):
    """Fetch meeting minutes for a given meeting ID."""
    try:
        response = supabase.table("meeting_minutes").select("*").eq("meeting_id", meeting_id).execute()
        if hasattr(response, 'error') and response.error:
            print("Error fetching meeting minutes:", response.error)
            return None
        return response.data
    except Exception as e:
        print("Exception fetching meeting minutes:", e)
        return None

if __name__ == "__main__":
    # Example data – replace with your real IDs
    meeting_data = {
        "organization_id": "9a6ac03d-2a3e-42b3-9e1d-1047055cd7a9",
        "meeting_code": "AUTO-" + time.strftime("%Y%m%d%H%M%S"),
        "title": "Automated Meeting - " + time.strftime("%Y-%m-%d %H:%M"),
        "scheduled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_mins": 60,
        "description": "Meeting created by automation",
    }

    result_meeting = add_meeting(meeting_data)
    print("Inserted meeting:", result_meeting)

    if result_meeting:
        meeting_id = result_meeting[0]["id"]

        attendee = {
            "meeting_id": meeting_id,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "type": "internal",
            "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        print("Inserted attendee:", add_meeting_attendee(attendee))

        minute = {
            "meeting_id": meeting_id,
            "mom_text": "Discussed project scope and deadlines.",
            "summary_text": "Project kickoff successful.",
            "transcript_text": "Full transcript text here..."
        }
        print("Inserted meeting minute:", add_meeting_minute(minute))
