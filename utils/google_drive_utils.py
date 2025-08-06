import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request


# Scope for Drive API - full access or set more limited scopes as needed
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Path to your client secret JSON downloaded from Google Cloud Console
CLIENT_SECRET_FILE = 'credentials.json'

def authenticate():
    creds = None
    # Token file stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If no valid credentials available, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save creds for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def upload_video(file_path, file_name=None):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    if not file_name:
        file_name = os.path.basename(file_path)

    media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)

    # Metadata for file (filename and mime type)
    file_metadata = {
        'name': file_name,
        # Optional: specify parent folder ID if you want to upload into a folder
        # 'parents': ['your_folder_id'],
    }

    # Upload file
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    print(f"Uploaded file ID: {file_id}")

    # Set permission to Anyone with the link can view
    permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    service.permissions().create(fileId=file_id, body=permission).execute()

    # Get shareable link (webViewLink)
    file_info = service.files().get(fileId=file_id, fields='webViewLink').execute()
    shareable_link = file_info.get('webViewLink')
    print(f"Shareable link: {shareable_link}")

    return file_id, shareable_link

if __name__ == '__main__':
    # Replace with your zoom video file path
    zoom_video_path = 'path_to_zoom_video.mp4'
    upload_video(zoom_video_path)
