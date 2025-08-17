import subprocess
import json
import base64
from datetime import datetime, timezone

def old_snapshot(event, context):
    """Triggered by a Pub/Sub message to delete old snapshots in a GCP project."""

    # Default values (can be overridden from Pub/Sub message)
    DAYS_THRESHOLD = 180
    project_id = None

    # Parse data from Pub/Sub message
    if 'data' in event:
        message_str = base64.b64decode(event['data']).decode('utf-8')
        try:
            payload = json.loads(message_str)
            project_id = payload.get("project_id", None)
            DAYS_THRESHOLD = int(payload.get("days_threshold", DAYS_THRESHOLD))
        except json.JSONDecodeError:
            print(f"Message data is not valid JSON: {message_str}")

    if not project_id:
        print("❌ No project_id provided in Pub/Sub message. Cannot proceed.")
        return

    print(f"📌 Starting snapshot cleanup for project '{project_id}' - Threshold: {DAYS_THRESHOLD} days")

    today = datetime.now(timezone.utc)

    # List snapshots
    list_cmd = f"gcloud compute snapshots list --project={project_id} --format=json"
    result = subprocess.run(list_cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0 or not result.stdout:
        print(f"⚠️ Error fetching snapshots for {project_id}: {result.stderr.strip()}")
        return

    snapshots = json.loads(result.stdout)
    deleted_snapshots = []

    for snap in snapshots:
        created_time = datetime.fromisoformat(snap["creationTimestamp"].replace("Z", "+00:00"))
        age_days = (today - created_time).days

        if age_days > DAYS_THRESHOLD:
            print(f"🗑 Deleting snapshot '{snap['name']}' (Age: {age_days} days)")
            delete_cmd = f"gcloud compute snapshots delete {snap['name']} --quiet --project={project_id}"
            delete_result = subprocess.run(delete_cmd, shell=True, capture_output=True, text=True)

            if delete_result.returncode == 0:
                deleted_snapshots.append({
                    "name": snap['name'],
                    "created": snap["creationTimestamp"],
                    "age_days": age_days
                })
            else:
                print(f"❌ Failed to delete {snap['name']}: {delete_result.stderr.strip()}")

    print(f"✅ Deleted {len(deleted_snapshots)} snapshots in project '{project_id}'")
    if deleted_snapshots:
        print(json.dumps(deleted_snapshots, indent=2))


