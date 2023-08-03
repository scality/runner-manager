# Backends

## Creating a new backend

Create a new file called, `runner_manager/backend/<backend name>.py`,
and implement a new class inheriting from `BaseBackend`.

The following methods need to be implemented:

- `create`
- `delete`
- `list`
- `get`

A configuration `BaseModel` will also need to be created in
`runner_manager/models/backend.py`, inheriting from `BackendConfig`.
