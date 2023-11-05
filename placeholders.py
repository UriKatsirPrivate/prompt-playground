TF_CONVERTER_PLACEHOLDER="""provider "aws" {
  region = "us-east-1"
}

# Creating a VPC
resource "aws_vpc" "my_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "my_vpc"
  }
}

# Creating a public subnet
resource "aws_subnet" "public" {
  vpc_id = aws_vpc.my_vpc.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}"""

INSPECT_IAC_PLACEHOLDER="""resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh"
  network = google_compute_network.default.name
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["77.125.87.177/32"]
  target_tags = ["allow-ssh"]
}"""

IMPROVE_PROMPT_PLACEHOLDER="list SecOps best practices"

INSPECT_PROMPT_PLACEHOLDER="### Expert in SecOps best practices, what are some best practices?"
RUN_PROMPT_PLACEHOLDER="### Expert in SecOps best practices, what are some best practices?"
GCLOUD_PLACEHOLDER="### Expert in GCP, create gcs bucket"
GENERATE_TF_PLACEHOLDER="### Expert in GCP, create gcs bucket"
GENERATE_IMAGES="A photo of a chocolate bar on a kitchen counter"
