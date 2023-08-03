# Backends

## Creating a new backend

Create a new file called, `runner_manager/backend/<backend name>.py`,
and implement a new class inheriting from `BaseBackend`.

Here's an example of a new backend:


```python
from runner_manager.backends.base import BaseBackend
from runner_manager.models.backend import BackendConfig, Backends

class MyBackendConfig(BackendConfig):
    # Configuration to communicate with the backend.
    pass

class MyBackendInstanceConfig(BackendInstanceConfig):
    # Specification and configuration of the backend instance.
    pass

class MyBackend(BaseBackend):
    name: Literal[Backends.mybackend] = Field(default=Backends.mybackend)
    config: MyBackendConfig
    instance_config: MyBackendInstanceConfig

```

The following methods need to be implemented:

- `create`: Create a new backend instance.
  This method must set the `instance_id` attribute of the backend instance.
- `delete`: Delete a backend instance.
- `update`: Update a backend instance.
- `list`: List all backend instances.
- `get`: Get a backend instance from a given instance_id


## Testing a new backend

Unit test can be written in `tests/unit/backend/test_<backend name>.py`.

If they require credentials, they should be skipped by default and only run
when the proper parameters are provided.
