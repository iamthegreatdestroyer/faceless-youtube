# Setup Wizard

This document describes how to run the interactive setup wizard for the
Faceless YouTube project.

## Running the wizard

- macOS / Linux:

```bash
./setup.sh
```

- Windows:

```batch
setup.bat
```

## Deployment modes

- Docker Full Stack (recommended): Spins up services in containers and
  generates `docker-compose.override.yml` alongside `.env`.
- Local Services (advanced): Use local Postgres/MongoDB/Redis instances.
- Hybrid: Mix of Docker + local services.

## Troubleshooting

- If you encounter missing packages, ensure the virtual environment is
  activated and `requirements-dev.txt` is installed.
- For Docker mode, verify Docker is installed and the current user has
  permission to run Docker commands.
