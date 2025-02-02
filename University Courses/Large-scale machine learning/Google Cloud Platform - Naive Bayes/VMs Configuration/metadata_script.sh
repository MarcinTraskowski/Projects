#!/bin/bash

# Generate ssh key pair
export GCP_userID="name_surname"  # your GCP_userID is your google login where . are replaced with _

mkdir .ssh
ssh-keygen -t ed25519 -f .ssh/id_gcp -N '' -C $GCP_userID

cat > transform_key.tf <<- EOM
resource "google_compute_project_metadata" "default" {
  metadata = {
    ssh-keys = <<EOF
EOM
echo -n "      $GCP_userID:" >> transform_key.tf
cat .ssh/id_gcp.pub >> transform_key.tf
cat >> transform_key.tf <<- EOM
    EOF
  }
}
EOM