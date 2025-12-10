# Fortaleza BID Monitor (Radar do Pici)

A Python microservice that monitors the CBF BID (Boletim Informativo Diário) for new contracts related to **Fortaleza Esporte Clube** and publishes updates to **Twitter (X)** and **Threads**.

## Features

- 🔍 **Automated Monitoring**: Checks CBF's BID every hour.
- 🤖 **AI Content Generation**: Uses Google Gemini to summarize contract details into engaging social media posts.
- 🐦 **Multi-Platform**: Posts to Twitter and Threads.
- 🔁 **Resilient**: Retries failed posts (e.g., due to rate limits) in the next cycle.
- 🌐 **Self-Hosted**: Designed to run via Docker Compose with Cloudflare Tunnel for secure external access.

## Local Setup

1.  **Clone the repo**:
    ```bash
    git clone https://github.com/tavares1/fortaleza-bid.git
    cd fortaleza-bid
    ```

2.  **Environment Variables**:
    Copy `.env.example` to `.env` and fill in your credentials.
    ```bash
    cp .env.example .env
    ```

3.  **Run with Docker**:
    ```bash
    docker-compose up --build
    ```

## Deployment (GitHub Actions)

This project is configured to deploy automatically to a self-hosted runner when you push to the `main` branch.

### 1. Self-Hosted Runner
Ensure your server is configured as a self-hosted runner for this repository.

### 2. GitHub Secrets
You must configure the following **Repository Secrets** in GitHub (`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`):

| Secret Name | Description |
| :--- | :--- |
| `GOOGLE_API_KEY` | Your Google Gemini API Key. |
| `TWITTER_API_KEY` | Twitter API Key (Consumer Key). |
| `TWITTER_API_SECRET` | Twitter API Secret (Consumer Secret). |
| `TWITTER_ACCESS_TOKEN` | Twitter Access Token. |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter Access Token Secret. |
| `THREADS_USER_ID` | Your Threads User ID. |
| `THREADS_ACCESS_TOKEN` | Your Threads Access Token. |
| `CLOUDFLARE_TUNNEL_TOKEN` | Token for cloudflared tunnel service. |
| `MONGO_URI` | (Optional) Full connection string if using external Mongo. |

### 3. Deploy
Simply push to main:
```bash
git push origin main
```
The workflow will:
1.  Checkout code on your server.
2.  Inject the secrets into a secure `.env` file.
3.  Rebuild and restart the containers.
