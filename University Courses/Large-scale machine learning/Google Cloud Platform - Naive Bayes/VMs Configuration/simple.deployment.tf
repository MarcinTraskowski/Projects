variable "project" {
  type = string
}

provider "google" {
  credentials = file("SERVICE_NAME.json")
  project     = var.project
  region      = "us-central1"
}


locals {
  zones  = ["us-central1-c", "us-east1-b", "us-east5-b", "us-west1-b"]
  regions = ["us-central1", "us-east1", "us-east5", "us-west1"]
}

resource "google_compute_address" "default" {
  count        = 20
  name         = "bml-${count.index}"
  region = element(local.regions, floor(count.index / 5)) # This must match the VM's region
}


resource "google_compute_instance" "vm_instance" {
  count        = 20
  name         = "bml-${count.index}"

  machine_type = "t2d-standard-1"
  zone         = element(local.zones, floor(count.index / 5))

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 20
    }
  }

  scheduling {
    preemptible       = true
    provisioning_model = "SPOT"
    automatic_restart = false
  }

  network_interface {
    network       = "default"
    access_config {
      nat_ip = google_compute_address.default[count.index].address
    }
  }
}



// A variable for extracting the external ip of the first instance
output "ip" {
 value = "${google_compute_instance.vm_instance[0].network_interface.0.access_config.0.nat_ip}"
}
