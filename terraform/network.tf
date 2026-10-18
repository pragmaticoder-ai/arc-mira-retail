# VPC Network for ARC
resource "google_compute_network" "arc_vpc" {
  name                    = "arc-vpc"
  auto_create_subnetworks = false
  description             = "VPC network for ARC services and databases"

  depends_on = [google_project_service.required_services]
}

# Subnet for general compute
resource "google_compute_subnetwork" "arc_subnet" {
  name          = "arc-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.arc_vpc.id
}

# Reserved internal IP range for Private Service Networking (Cloud SQL / AlloyDB)
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "arc-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.arc_vpc.id

  depends_on = [google_project_service.required_services]
}

# VPC Peering connection to Google services (AlloyDB / Cloud SQL)
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.arc_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]

  depends_on = [google_project_service.required_services]
}

# Serverless VPC Access Connector so Cloud Run can communicate privately with database
resource "google_vpc_access_connector" "arc_connector" {
  name          = "arc-vpc-conn"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.arc_vpc.name
  min_instances = 2
  max_instances = 3

  depends_on = [
    google_project_service.required_services,
    google_compute_network.arc_vpc
  ]
}
