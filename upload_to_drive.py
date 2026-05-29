import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

print("Uploading to Google Drive...")

creds_json = os.getenv("GOOGLE_DRIVE_CREDENTIALS")
folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

creds_dict = json.loads(creds_json)
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/drive"]
)

service = build("drive", "v3", credentials=creds)

# Check if file already exists in folder
results = service.files().list(
    q=f"'{folder_id}' in parents and name='hr_odds.xlsx' and trashed=false",
    spaces="drive",
    fields="files(id, name)",
    pageSize=1
).execute()

file_metadata = {"name": "hr_odds.xlsx"}
media = MediaFileUpload("hr_odds.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if results.get("files"):
    # Update existing file
    file_id = results["files"][0]["id"]
    service.files().update(fileId=file_id, media_body=media).execute()
    print(f"Updated existing file: hr_odds.xlsx")
else:
    # Create new file
    file_metadata["parents"] = [folder_id]
    service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"Created new file: hr_odds.xlsx")

print("Upload complete!")
