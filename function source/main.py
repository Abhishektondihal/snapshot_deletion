import base64
import datetime
import json
from googleapiclient import discovery
from google.auth import default

def delete_old_snapshots(event, context):
    # Get project_id from Pub/Sub message
    if 'data' in event:
        message = base64.b64decode(event['data']).decode('utf-8')
        payload = json.loads(message)
        project_id = payload['project_id']
    else:
        raise Exception("No project_id found in message.")

    credentials, _ = default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=180)
    deleted_count = 0

    print(f"Checking snapshots in project {project_id} older than {cutoff_date.date()}...")

    next_page_token = None
    while True:
        results = compute.snapshots().list(project=project_id, pageToken=next_page_token).execute()
        for snapshot in results.get('items', []):
            creation_time = datetime.datetime.fromisoformat(snapshot['creationTimestamp'].replace('Z', '+00:00'))
            if creation_time < cutoff_date:
                print(f"Deleting snapshot: {snapshot['name']} (created: {creation_time})")
                compute.snapshots().delete(project=project_id, snapshot=snapshot['name']).execute()
                deleted_count += 1
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break

    print(f"Deletion complete. Total snapshots deleted: {deleted_count}")
