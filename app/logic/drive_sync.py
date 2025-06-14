import os
import json
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_PATH = '../drive/credentials.json'
TOKEN_PATH = '../drive/token.json'

def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(local_path, drive_filename):
    service = get_drive_service()
    file_metadata = {'name': drive_filename}
    media = MediaFileUpload(local_path, mimetype='text/plain')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def download_file_from_drive(file_name, save_path):
    service = get_drive_service()
    results = service.files().list(q=f"name='{file_name}' and trashed=false",
    spaces='drive',
    fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        raise FileNotFoundError(f"{file_name} がGoogleドライブに見つかりませんでした。")
    file_id = items[0]['id']
    request = service.files().get_media(fileId=file_id)
    with open(save_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return save_path