provider "google" {
  project = var.project
  region  = var.region
}

resource "google_pubsub_topic" "snapshots_trigger" {
  name = "delete-old-snapshots"
}

resource "google_cloudfunctions2_function" "delete_old_snapshots" {
  name     = "delete-old-snapshots"
  location = var.region

  build_config {
    runtime     = "python310"
    entry_point = "delete_old_snapshots" # Should match your function in main.py

    source {
      local_path = "${path.module}/function-source"
    }
  }

  service_config {
    min_instance_count    = 0
    max_instance_count    = 1
    available_memory      = "256M"
    timeout_seconds       = 540
    ingress_settings      = "ALLOW_ALL"
    all_traffic_on_latest_revision = true
  }

  event_trigger {
    event_type   = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic = google_pubsub_topic.snapshots_trigger.id
    retry_policy = "RETRY_POLICY_RETRY"
  }

  depends_on = [google_pubsub_topic.snapshots_trigger]
}

