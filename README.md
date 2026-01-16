# 🚀 Cloud-Native URL Analytics Platform

**A scalable, containerized URL shortening service with real-time analytics, AI insights, and centralized observability.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9-blue.svg)
![Docker](https://img.shields.io/badge/docker-containerized-blue.svg)
![Terraform](https://img.shields.io/badge/terraform-GCP-purple.svg)
![Redis](https://img.shields.io/badge/redis-caching-red.svg)
![ELK](https://img.shields.io/badge/ELK-observability-orange.svg)

---

## 🧠 What is this?

This project is a **production-ready demonstration** of modern DevOps and Cloud-Native practices. It is not just a URL shortener; it is a full-stack engineering showcase that mimics large-scale system architectures using **Free-Tier** resources.

### ✨ Key Features
*   **🔗 URL Shortening**: Deterministic short codes using MD5 hashing.
*   **⚡ Ultra-Fast Caching**: **Redis** is used for caching hot URLs and counting hits in real-time.
*   **🤖 AI-Powered Insights**: Integrates **Google Vertex AI (Gemini Pro)** to automatically categorize and summarize the content of shortened links in the background.
*   **👁️ Centralized Observability**: Full **ELK Stack (Elasticsearch, Logstash, Kibana)** integration for structured logging and traffic visualization.
*   **☁️ Infrastructure as Code**: Entire GCP infrastructure (Compute, Network, Firewall) provisioned via **Terraform**.
*   **🔄 CI/CD Pipeline**: Fully automated **GitHub Actions** workflows for Linting, Docker Build, Security Scanning (Trivy), and Terraform Deployment.

---

## 🏗️ Architecture

1.  **Application**: Python FastAPI (High performance, Async).
2.  **Data Layer**: Redis (Primary store for mappings and active analytics).
3.  **Intelligence**: Google Vertex AI (Gemini Pro) for content classification.
4.  **Logging**: Python App -> Logstash (TCP) -> Elasticsearch -> Kibana.
5.  **Infrastructure**: Docker Containers running on Google Compute Engine (e2-micro).

---

## 🚀 Getting Started (Local)

### Prerequisites
*   Docker & Docker Compose
*   Google Cloud Service Account Key (for AI features)

### 1. Clone the Repo
```bash
git clone https://github.com/nshivakumar1/Cloud-Native-URL-Analytics-Platform.git
cd Cloud-Native-URL-Analytics-Platform
```

### 2. Configure Credentials (Optional for AI)
To enable Gemini AI features, place your GCP Service Account JSON key in the root directory:
```bash
# Rename your downloaded key
mv ~/Downloads/my-key.json ./gcp_credentials.json
```
*Note: The app runs fine without this, but AI features will be disabled.*

### 3. Run with Docker Compose
```bash
docker-compose up -d --build
```

### 4. Verify
*   **API**: `http://localhost:8000/docs`
*   **Kibana**: `http://localhost:5601`

---

## 🛠️ Usage

### Shorten a URL
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"url": "https://www.nasa.gov"}' \
     http://localhost:8000/shorten
```
**Response:**
```json
{
  "short_code": "a1b2c3",
  "original_url": "https://www.nasa.gov"
}
```

### Get Stats & AI Insights
```bash
curl http://localhost:8000/stats/a1b2c3
```
**Response:**
```json
{
  "visits": 42,
  "ai_insights": {
    "category": "Science & Technology",
    "summary": "Official website of the National Aeronautics and Space Administration."
  }
}
```

---

## ☁️ Deployment (GCP)

### 🟢 Live Demo
The application is currently deployed and active on Google Cloud:
**👉 [http://34.173.226.60](http://34.173.226.60)**

This project uses **Terraform** to provision infrastructure on Google Cloud Platform.

1.  **Set Secrets in GitHub**:
    *   `GCP_CREDENTIALS`: Your Service Account JSON.
    *   `TF_VAR_project_id`: Your GCP Project ID.
2.  **Push to Main**:
    *   GitHub Actions will trigger the **CD Pipeline**.
    *   Terraform `plan` and `apply` will run automatically.

---

## 📂 Project Structure

```bash
.
├── app/                 # FastAPI Application & Dockerfile
├── elk/                 # Logstash & Kibana Configuration
├── terraform/           # IaC for GCP (Compute, VPC, Firewall)
├── .github/workflows/   # CI/CD Pipelines
├── docker-compose.yml   # Local Development Setup
└── README.md
```
