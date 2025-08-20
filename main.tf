provider "google" {
  project = var.project
  region  = var.region
}

resource "google_pubsub_topic" "snapshots_trigger" {
  name = "delete-old-snapshots"
}

resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project}-functions-bucket"
  location = var.region
  force_destroy = true
}

resource "google_storage_bucket_object" "function_zip" {
  name   = "main.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "${path.module}/function-source/main.zip"
}

resource "google_cloudfunctions2_function" "delete_old_snapshots" {
  name     = "delete-old-snapshots"
  location = var.region

  build_config {
    runtime     = "python310"
    entry_point = "delete_old_snapshots"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket.name
        object = google_storage_bucket_object.function_zip.name
      }
    }
  }

  service_config {
    min_instance_count               = 0
    max_instance_count               = 1
    available_memory                 = "256M"
    timeout_seconds                  = 540
    ingress_settings                 = "ALLOW_ALL"
    all_traffic_on_latest_revision   = true
  }

  event_trigger {
    event_type   = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic = google_pubsub_topic.snapshots_trigger.id
    retry_policy = "RETRY_POLICY_RETRY"
  }

  depends_on = [google_pubsub_topic.snapshots_trigger]
}


