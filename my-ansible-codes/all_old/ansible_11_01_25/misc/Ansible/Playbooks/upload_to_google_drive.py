from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# SCOPES required for file upload
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def upload_to_google_drive(output_file, file_name):
    # Load credentials from the service account file
    creds = service_account.Credentials.from_service_account_file(
        '/mnt/d/networking/network-automation/boot-camp/ansible-may-24/Ansible/Playbooks/service_account.json',
        scopes=SCOPES
    )

    # Build the Drive API client
    drive_service = build('drive', 'v3', credentials=creds)

    # Folder ID where the file will be uploaded
    folder_id = '1Y_nSmni0Rasoh2ly7HcnxYuKRMsvN8qC'

    # Metadata for the file, specifying the folder ID
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    # Upload the file using MediaFileUpload
    media = MediaFileUpload(output_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # Create and upload the file
    file = drive_service.files().create(
        media_body=media,
        body=file_metadata,
    ).execute()

    # Corrected print statement
    print(f"File uploaded successfully with ID: {file['id']}")

# Call the function to upload the file
upload_to_google_drive('/mnt/d/networking/network-automation/boot-camp/ansible-may-24/Ansible/Playbooks/switch_interfaces_report.xlsx', 'switch_interfaces_report.xlsx')