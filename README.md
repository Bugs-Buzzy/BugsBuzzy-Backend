# BugsBuzzy-Backend

Backend for the "BugsBuzzy" GameJam Event, hosted by the CE department at Sharif University of Technology. This project is built using Django and Django REST Framework to provide a robust RESTful API.

## Core Technologies

- **Backend Framework**: Django
- **API**: Django REST Framework (DRF)
- **Authentication**: Simple JWT for token-based authentication
- **Database**: PostgreSQL (configured with `dj-database-url`)
- **API Schema/Docs**: `drf-spectacular` for OpenAPI 3 schema generation (Swagger UI/ReDoc)
- **Package Management**: PDM
- **Containerization**: Docker & Gunicorn
- **Testing**: Pytest

## Project Structure

The project is organized into several Django apps, each responsible for a specific domain:

- `core/`: Contains the main project configuration, settings, and URL routing.
- `accounts/`: Manages user registration, authentication, profiles, and permissions.
- `announcement/`: Handles creating and displaying announcements.
- `gamejam/`: Core logic related to the GameJam event itself.
- `inperson/`: Manages in-person event logistics.
- `leaderboard/`: Provides leaderboard functionality.
- `lobbygame/`: Functionality for the game lobby.
- `minigame/`: Manages mini-games within the event.
- `payments/`: Handles payment processing and history.
- `workshops/`: Manages workshop schedules and registration.

## Getting Started

### Prerequisites

- Python 3.10+
- PDM (Python Dependency Manager)
- Docker (optional, for containerized setup)

### Local Development Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Bugs-Buzzy/BugsBuzzy-Backend.git
    cd BugsBuzzy-Backend
    ```

2.  **Install dependencies using PDM:**
    If you don't have PDM, install it first: `pip install --user pdm`.
    ```bash
    pdm install
    ```

3.  **Set up environment variables:**
    Create a `.env` file by copying the example file and fill in the required values (e.g., database URL, secret key).
    ```bash
    cp .env.example .env
    ```

4.  **Apply database migrations:**
    ```bash
    pdm run python manage.py migrate
    ```

5.  **Run the development server:**
    ```bash
    pdm run python manage.py runserver
    ```
    The server will be available at `http://127.0.0.1:8000`.

## API Documentation

With the development server running, you can access the auto-generated API documentation:

- **Swagger UI**: `http://127.0.0.1:8000/docs/`
- **ReDoc**: `http://127.0.0.1:8000/redoc/`
- **Schema YAML**: `http://127.0.0.1:8000/schema/`

## Running with Docker

You can build and run the application using Docker for a containerized environment.

1.  **Build the Docker image:**
    ```bash
    docker build -t bugsbuzzy-backend .
    ```

2.  **Run the container:**
    Make sure you have a `.env.prod` file with production-ready settings.
    ```bash
    docker run --env-file .env.prod -p 8000:8000 bugsbuzzy-backend
    ```

## Testing

This project uses `pytest` for testing. To run the test suite:

```bash
pdm run pytest
```

To view test coverage:

```bash
pdm run pytest --cov
```
