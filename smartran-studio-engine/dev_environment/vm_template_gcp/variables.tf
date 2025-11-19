variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "The region for resources"
  type        = string
}

variable "zone" {
  description = "The zone for the VM"
  type        = string
}

variable "instance_name" {
  description = "The name of the VM instance"
  type        = string
}

variable "machine_type" {
  description = "The machine type for the VM"
  type        = string
  default     = "e2-standard-4"
}

variable "vpc_network" {
  description = "The VPC network name"
  type        = string
}

variable "subnet" {
  description = "The subnet within the VPC"
  type        = string
}

variable "image_project" {
  description = "The GCP project for the image"
  type        = string
}

variable "image_family" {
  description = "The image family for the boot disk"
  type        = string
}

variable "ssh_tag" {
  description = "The tag to associate with the VM for firewall rules"
  type        = string
}

variable "startup_script" {
  description = "The startup script to run on the VM (e.g., install GitLab Runner)"
  type        = string
}

variable "gpu_type" {
  description = "Type of GPU you want to install"
  type        = string
}


variable "gpu_count" {
  description = "Amount of GPU you want associated with your VM"
  type        = string
}

variable "storage_type" {
  description = "Storage type of the SSD"
  type        = string
}


