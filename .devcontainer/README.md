# Codespace

Here are the list of commands that work out of the box in
the available codespace.

## Linting and formatting

To format or lint the codebase, run the following commands:

```bash
trunk fmt # for formatting
trunk check # for linting
```

## Tests

Tests can be run with the following command:

```bash
poetry run pytest tests # Run all tests
poetry run pytest tests/unit # Run unit tests
poetry run pytest tests/api # Run api tests
```

## Local environment

To bootstrap a local environment, run the following command:

```bash
docker compose --profile dev up --build
```
