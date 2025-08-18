resource "google_pubsub_topic" "snapshots_trigger" {
  name = "delete-old-snapshots"
}

resource "google_cloudfunctions_function" "delete_old_snapshots" {
  name        = "delete-old-snapshots"
  runtime     = "python310"
  entry_point = "delete_old_snapshots"
  ...
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.snapshots_trigger.id
  }
}
