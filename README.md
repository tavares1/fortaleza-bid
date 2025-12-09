# CBF Captcha Solver

This project fetches a captcha from cbf.com.br and solves it using Google's Gemini AI.

## Prerequisites

- Docker
- A Google Cloud API Key with access to Gemini API.

## Setup

1.  Clone this repository or navigate to the directory.
2.  Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```
3.  Open `.env` and fill in the required values:
    - `GOOGLE_API_KEY`: Your Gemini API Key (Required).

    > **Note**: Even if you don't provide the CBF tokens, the script will attempt to fetch the captcha. Any new cookies received from the server will be printed to the console.

## Running with Docker

1.  **Build the image**:
    This creates a Docker image named `cbf-solver` containing the application and its dependencies.
    ```bash
    docker build -t cbf-solver .
    ```

2.  **Run the container**:
    This runs the script inside the container. We pass the `.env` file to provide the necessary variables.
    ```bash
    docker run --rm --env-file .env cbf-solver
    ```
    *The `--rm` flag automatically removes the container after it exits to keep your system clean.*

## Output

The script will output the solving process logs, including any new cookies received from the server, and finally the solved text:

```text
Fetching captcha...
Cookies received from server:
cookiesession1: <value>
...
Captcha fetched (length: 1234). Solving...
--------------------
CAPTCHA SOLVED: <The Text>
--------------------
```
