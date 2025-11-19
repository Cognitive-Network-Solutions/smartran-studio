# Configure the Google Cloud provider with the specified project and region
provider "google" {
  project = var.project_id
  region  = var.region
}

# -----------------------------------------
# 🏗️ Create Service Account for the VM
# -----------------------------------------
resource "google_service_account" "vm_service_account" {
  account_id   = "${var.instance_name}-sa"
  display_name = "AI Training VM Service Account"
}

# Assign "Compute Viewer" role to the Service Account 
# Allows the VM to view compute resources but not modify them
resource "google_project_iam_member" "vm_sa_compute_viewer" {
  project = var.project_id
  role    = "roles/compute.viewer"
  member  = "serviceAccount:${google_service_account.vm_service_account.email}"
}

# Assign "Secret Accessor Role" role to the Service Account
resource "google_project_iam_member" "vm_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.vm_service_account.email}"
}

# -----------------------------------------
# 🚀 Create The VM
# -----------------------------------------
resource "google_compute_instance" "vm_instance" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  # Attach VM to the specified VPC network and subnet
  network_interface {
    network    = var.vpc_network
    subnetwork = var.subnet
  }

  # Attach the service account to the VM with full API access (IAM controls permissions)
  service_account {
  email  = google_service_account.vm_service_account.email
  scopes = ["cloud-platform"]  # Full API access, but controlled by IAM
  }

  # Configure the VM's boot disk with the specified image and size (100GB)
  boot_disk {
    initialize_params {
      image = "${var.image_project}/${var.image_family}"
      size  = 500  # Set the disk size to 100GB (or adjust as needed)
      type = var.storage_type
    }
  }

  # 🚀 New Block: Attach GPU (A100 for example)
  guest_accelerator {
    type  = var.gpu_type  # example: "nvidia-tesla-a100"
    count = var.gpu_count # example: 1
  }
  
  # Guest accelerator doesnt support live migration
  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = true
  }


  # Execute the startup script when the VM is create
  metadata_startup_script = file(var.startup_script)


  # Apply a dynamic tag to the VM for firewall rule enforcement
  tags = [var.ssh_tag]  # Apply dynamic tag from variable

}




# -----------------------------------------
# 🔐 Create SSH Firewall Rule for the VM
# -----------------------------------------
resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.instance_name}-allow-iap-ssh" 
  network = var.vpc_network

  # Allow SSH access on port 22
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # Restrict SSH access to Google's IAP IP range for security
  source_ranges = ["35.235.240.0/20"]  # Restrict SSH to Google's specific IAP 

  # Apply the rule only to VMs with the specified tag
  target_tags = [var.ssh_tag]  # Use the same tag for consistency
}