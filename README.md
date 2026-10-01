# Schoology API Explorer

A local, read-only dashboard for exploring the Schoology API with OAuth 1.0a credentials. The application provides a curated endpoint catalog, authenticated request testing, response inspection, resource discovery, and a bounded API scan without exposing credentials to the browser.

This project is intended for development, integration testing, and API discovery. It is not a replacement for Schoology's production administration tools.

## Features

- Test the configured credentials with `GET /v1/users/me`.
- Browse the endpoint catalog by category and provide IDs for resource endpoints.
- Run custom `GET` requests against approved `/v1/...` API paths.
- Inspect status, response classification, elapsed time, redirects, final URL, and response JSON.
- Discover users and inspect related user resources.
- Load the authenticated user's sections and view section assignments.
- Run a background, read-only scan of the catalog and review progress and classifications.
- Review request history for the current process and reopen a previous response.

## Requirements

- Python 3.10 or newer
- A Schoology API consumer key and consumer secret with permission to access the desired resources
- Network access to `https://api.schoology.com`

## Setup

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root. Do not commit it:

```dotenv
SCHOOLOGY_CONSUMER_KEY=your-consumer-key
SCHOOLOGY_CONSUMER_SECRET=your-consumer-secret
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> in a browser and select **Test authentication** before making other requests.

## How requests are handled

All Schoology requests are signed server-side with OAuth 1.0a. The browser sends paths to the FastAPI application; credentials are never sent to the browser. The application accepts only paths under `/v1/` on `api.schoology.com`, rejects traversal and unsafe path characters, performs `GET` requests only, and follows up to five redirects while re-signing each hop. Redirects that leave the Schoology API host are rejected.

The endpoint catalog is maintained in [app/endpoints.py](app/endpoints.py). It currently includes users, schools, districts, courses, sections, groups, assignments, documents, events, messages, grades, discussions, pages, and roles. Add or verify catalog entries there before using them in a scan.

## Application API

The dashboard uses these local routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Serve the dashboard |
| `GET` | `/api/endpoints` | Return endpoint categories and catalog |
| `POST` | `/api/request` | Execute one validated Schoology `GET` request |
| `POST` | `/api/auth-test` | Request the current authenticated user |
| `GET` | `/api/history` | List request metadata for this process |
| `GET` | `/api/history/{index}` | Retrieve one stored response |
| `POST` | `/api/scan` | Start the background catalog scan |
| `GET` | `/api/scan/status` | Return scan progress and classifications |

## Scan configuration

The scan runs in a daemon thread and defaults to a maximum of 100 requests with a 250 ms delay between requests. Override these values in `.env` when needed:

```dotenv
MAX_REQUESTS_PER_SCAN=100
REQUEST_DELAY_MS=250
```

The scan skips the list endpoints for courses, sections, and districts, then uses IDs discovered from successful responses for ID-based endpoints. It limits each discovered resource kind to five IDs. These controls help avoid accidental request bursts, but API permissions and rate limits still apply.

## Data and deployment notes

- Request history and scan state are stored only in memory and are lost when the process restarts.
- The server does not provide user authentication or multi-user isolation. Keep it on localhost or place it behind an authenticated, trusted network boundary before exposing it.
- Responses may contain sensitive student or course data. Handle logs, screenshots, and copied JSON accordingly.
- Schoology permissions determine which resources are available; a `403`, `404`, or empty response can be a valid result for a configured endpoint.

## Development

Run a syntax check before publishing changes:

```bash
python -m compileall app
```

The application is built with FastAPI, Jinja2, vanilla JavaScript, and CSS. There is currently no automated test suite in the repository.
