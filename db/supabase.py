import time
from supabase import create_client, Client
import config  # Your config.py where SUPABASE_URL and SUPABASE_KEY are defined


SUPABASE_URL = config.SUPABASE_URL
SUPABASE_KEY = config.SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase URL and KEY must be set in config.py")


# Initialize Supabase client once
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def add_meeting(meeting_data: dict):
    """
    Insert a new meeting record.

    Parameters:
        meeting_data (dict): Meeting details.

    Returns:
        list or None: Inserted meeting row(s) or None if failure.
    """
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
    """
    Insert a meeting attendee record.

    Parameters:
        attendee_data (dict): Attendee details with keys like meeting_id, email, type, sent_at.

    Returns:
        list or None: Inserted attendee row(s) or None if failure.
    """
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
    """
    Insert meeting minute record.

    Parameters:
        minute_data (dict): Meeting minute details.

    Returns:
        list or None: Inserted minute row(s) or None if failure.
    """
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
    """
    Fetch all meetings.

    Returns:
        list or None: Meeting rows or None if failure.
    """
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
    """
    Fetch attendees for a given meeting ID.

    Parameters:
        meeting_id (str): Meeting UUID.

    Returns:
        list or None: Attendee rows or None if failure.
    """
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
    """
    Fetch meeting minutes for a given meeting ID.

    Parameters:
        meeting_id (str): Meeting UUID.

    Returns:
        list or None: Meeting minute rows or None if failure.
    """
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
    # Example usage - replace with your actual IDs and data

    meeting_data = {
        "organization_id": "9a6ac03d-2a3e-42b3-9e1d-1047055cd7a9",  # Replace with your real org ID
        "meeting_code": "AUTO-" + time.strftime("%Y%m%d%H%M%S"),
        "title": "Automated Meeting - " + time.strftime("%Y-%m-%d %H:%M"),
        "scheduled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_mins": 60,
        "description": "Meeting created by automation",
    }

    # Insert meeting
    result_meeting = add_meeting(meeting_data)
    print("Inserted meeting:", result_meeting)

    if result_meeting:
        meeting_id = result_meeting[0]["id"]

        # Example attendee
        attendee = {
            "meeting_id": meeting_id,
            "name": "John Doe",              # Adjust if you track names
            "email": "john.doe@example.com",
            "type": "internal",              # Optional: track internal or external
            "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        result_attendee = add_meeting_attendee(attendee)
        print("Inserted attendee:", result_attendee)

        # Example meeting minute
        minute = {
            "meeting_id": meeting_id,
            "mom_text": "Discussed project scope and deadlines.",
            "summary_text": "Project kickoff successful.",
            "transcript_text": "Full transcript text here..."
        }
        result_minute = add_meeting_minute(minute)
        print("Inserted meeting minute:", result_minute)
