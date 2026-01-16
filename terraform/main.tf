terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# VPC Network
resource "google_compute_network" "vpc_network" {
  name                    = "url-analytics-vpc"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "url-analytics-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

# Firewall Rules
resource "google_compute_firewall" "allow_web" {
  name    = "allow-web"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web-server"]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web-server"]
}

# Compute Instance
resource "google_compute_instance" "app_server" {
  name         = var.instance_name
  machine_type = "e2-micro"
  zone         = var.zone
  tags         = ["web-server"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id
    access_config {
      # Ephemeral public IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose git
    systemctl enable docker
    systemctl start docker
    # Clone repo would go here, or we can use SCP/CI-CD to deploy
  EOF

  metadata = {
    ssh-keys = "runner:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDXp3uhoFFShJjOQsBtfqpqo4VjzCTtRbMrxoj6Z7FZRiVRD0y2Q5EqwzC5x04JowdWRk/v3YQ+Fu8p4aN2gA/8bR7+A0TTTpBKuZmX6AMLgKttQWygHzXxXqIJrEs/K/LhS1LIqVHYzPNQ1IH9N9IXWn7DF0NFjBn+Qst7Lbrhykkode7viblRD17SXXH1RQr5gGbKtsLwJhlw4Qx7dWa2ih1Re8VC+1hZCyh23k+XvJZuvyuX5o5n3QoN57BIYiNLXLGX157uPIrqIhwFXL+xCj6uGI4/4BoYc+luS9ZIOhoQcM9/umo/MyjJenEdkIx3jP2WEj7t8KryYHzpZh9Hm2+ATQXrHr4nSYxpdqd+VnyA6+VD3FUK2D9//hjnWrvQx84ebfG/jeYfNYVbCcfCcMT7cJhGjy8OrK9wxgwviXRoA79CNbHZlD4eBcQfscmdNGJ1r9N04GcA01oaFG7NJQxX0YINj6niZ+ihB2hXbq5VPEPUbpIw2ZSfJ/3heXhkpDyuVRfAy/2GoAKDvvAuAlCXsW00TyDUw1xpIK0uEc3btE2MV6gfxs9XhmOXYJjFDEn+Jz33rQ5O/k92zFeaD87kBqb6cfG+ufnRv6gVxNQT11CvuvQx9YjuDrnfyAewVGZq5NYyQJPoTXUjK0HoBrcjAKgdsB2I9FVEGZRoMw== runner"
  }
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "url-analytics-repo"
  description   = "Docker repository for URL Analytics Platform"
  format        = "DOCKER"
}
