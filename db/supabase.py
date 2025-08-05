from supabase import create_client, Client
import config  # Import your config.py where SUPABASE_URL and SUPABASE_KEY are defined

SUPABASE_URL = config.SUPABASE_URL
SUPABASE_KEY = config.SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase URL and KEY must be set in config.py")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_meeting(meeting_data: dict):
    try:
        response = supabase.table("meetings").insert(meeting_data).execute()
        # response.data contains inserted rows
        return response.data
    except APIError as e:
        print("Error adding meeting:", e)
        return None


def add_meeting_attendee(attendee_data: dict):
    response = supabase.table("meeting_attendees").insert(attendee_data).execute()
    if response.error:
        print("Error adding attendee:", response.error)
        return None
    return response.data

def add_meeting_minute(minute_data: dict):
    try:
        response = supabase.table("meeting_minutes").insert(minute_data).execute()
        # Inserted data accessible via response.data
        return response.data
    except APIError as e:
        print("Error adding meeting minute:", e)
        return None

def get_meetings():
    response = supabase.table("meetings").select("*").execute()
    if response.error:
        print("Error fetching meetings:", response.error)
        return None
    return response.data

def get_meeting_attendees(meeting_id):
    response = supabase.table("meeting_attendees").select("*").eq("meeting_id", meeting_id).execute()
    if response.error:
        print("Error fetching attendees:", response.error)
        return None
    return response.data

def get_meeting_minutes(meeting_id):
    response = supabase.table("meeting_minutes").select("*").eq("meeting_id", meeting_id).execute()
    if response.error:
        print("Error fetching meeting minutes:", response.error)
        return None
    return response.data

# Example usage
if __name__ == "__main__":
    # Replace keys and values according to your actual table schema
 
    meeting_data = {
        "organization_id": "9a6ac03d-2a3e-42b3-9e1d-1047055cd7a9",  # Example, replace with actual ID
        "meeting_code": "AUTO-" + time.strftime("%Y%m%d%H%M%S"),  # unique code example
        "title": "Automated Meeting - " + time.strftime("%Y-%m-%d %H:%M"),
        "scheduled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_mins": 60,  # example duration, you can set dynamically
        "description": "Meeting created by automation",
    }




    result_meeting = add_meeting(meeting)
    print("Inserted meeting:", result_meeting)

    if result_meeting:
        meeting_id = result_meeting[0]["id"]

        attendee = {
            "meeting_id": meeting_id,
            "name": "John Doe",
            "email": "john.doe@example.com"
        }
        result_attendee = add_meeting_attendee(attendee)
        print("Inserted attendee:", result_attendee)

        minute = {
            "meeting_id": meeting_id,
            "mom_text": "Discussed project scope and deadlines.",
            "summary_text": "Project kickoff successful.",
            "transcript_text": "Full transcript text here..."
        }
        result_minute = add_meeting_minute(minute)
        print("Inserted meeting minute:", result_minute)
