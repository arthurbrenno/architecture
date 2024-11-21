# 🧵 Architecture - The Clean Backend for All Architectures

From dictionary
> an introduction to something more substantial.

Architecture is a robust and flexible backend framework designed to streamline the development of scalable and maintainable applications. Leveraging modern Python features and best practices, Architecture provides a comprehensive set of tools and modules to handle logging, data management, services, repositories, and more. Whether you're building a simple API or a complex microservices architecture, Architecture offers the foundation you need to succeed.

## Table of Contents

- [Key Components](#key-components)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Modules](#modules)
  - [Logging](#logging)
  - [Data](#data)
  - [Services](#services)
  - [Utils](#utils)
- [Deprecation Notice](#deprecation-notice)
- [Migration Guide](#migration-guide)
- [Usage Examples](#usage-examples)
  - [Creating a Service](#creating-a-service)
  - [Defining a Repository](#defining-a-repository)
  - [Using the Logging Module](#using-the-logging-module)
- [Contributing](#contributing)
- [License](#license)

## Key Components

Architecture is built around several core classes that provide the foundation for its functionality:

### **BaseModel**

A base class for all data schemas in Architecture, extending `msgspec.Struct`. It provides fast serialization/deserialization capabilities and utility methods for JSON handling.

### **Entity**

An abstract base class representing entities in the application. Entities are foundational data objects with optional identifiers and creation timestamps.

### **ValueObject**

An abstract base class for immutable value objects used to describe entities. They encapsulate attributes without unique identifiers.

### **Repository & AsyncRepository**

Abstract base classes defining interfaces for data access operations. `Repository` is for synchronous operations, while `AsyncRepository` supports asynchronous operations. They provide methods for CRUD operations, ensuring a consistent interface across different data sources.

### **Service & AsyncService**

Abstract base classes for defining business logic encapsulation. `Service` is for synchronous services, and `AsyncService` is for asynchronous services. They require implementation of the `execute` method, which contains the core business logic.

### **ServiceExecutor**

A utility class responsible for executing both synchronous and asynchronous services. It provides a unified interface to invoke services seamlessly, handling the differences between synchronous and asynchronous execution.

### **ConstContainer**

An immutable container class using `BaseModel`. It provides a base for creating constant containers with type safety and memory efficiency.

### **DynamicDict**

A builder class that simplifies the construction of dynamic dictionaries. It offers methods to incrementally build dictionaries with a fluent interface.

### **DynamicInstanceCreator**

A utility class for creating class instances with dynamic parameters. It inspects the constructor of classes to initialize instances with the maximum number of possible parameters, handling unexpected keyword arguments gracefully.

### **TempFile**

An asynchronous context manager and decorator for handling temporary file operations in FastAPI applications. It ensures that temporary files are properly managed and cleaned up after usage.

### **Decorators (`pure`, `deprecated`)**

Utility decorators to enhance functions with caching (`pure`) and deprecation warnings (`deprecated`). They provide reusable functionality to optimize performance and manage code evolution.

### **Logger**

A configured logger based on Loguru and Rich, providing colorful and structured logging throughout the application. It supports different log levels and integrates with Rich's traceback for improved error visibility.

## Features

- **Advanced Logging**: Integrated with Loguru and Rich for colorful and structured logging.
- **Data Management**: Robust schemas and repositories for handling data operations.
- **Service Layer**: Abstracted service classes for business logic encapsulation.
- **Utilities**: A suite of utility functions and decorators to enhance development productivity.
- **Type Safety**: Comprehensive type annotations and type stubs for reliable and maintainable code.
- **Extensible Architecture**: Modular design allowing easy extension and customization.

## Installation

Architecture can be installed via `pip` from PyPI. Ensure you have Python 3.10 or higher.

```bash
pip install architecture
```

Alternatively, you can install it directly from the repository:

```bash
git clone https://github.com/arthurbrenno/architecture.git
cd architecture
pip install -e .
```

## Quick Start

Here's a quick example to get you started with Architecture. This example demonstrates setting up logging, defining a data model, creating a service, and executing it.

```python
import asyncio
from architecture.logging import logger
from architecture import BaseModel
from architecture.services import Service, ServiceExecutor
from architecture.data.repositories import Repository, CreateResult, ReadResult, ReadAllResult, UpdateResult, DeleteResult

# Define a data model
class User(BaseModel):
    username: str
    email: str

# Define a repository interface
class UserRepository(Repository[User]):
    pass

# Implement the repository
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self.users = {}

    async def create(self, entity: User, *, filters: dict = None) -> CreateResult:
        self.users[entity.username] = entity
        return CreateResult(uid=entity.username)

    async def read(self, q: str, *, filters: dict = None) -> ReadResult[User]:
        user = self.users.get(q)
        return ReadResult(entity=user)

    async def read_all(self, *, filters: dict = None) -> ReadAllResult[User]:
        return ReadAllResult(entities=list(self.users.values()))

    async def update(self, q: str, entity: User, *, filters: dict = None) -> UpdateResult:
        if q in self.users:
            self.users[q] = entity
            return UpdateResult(affected_records=1)
        return UpdateResult(affected_records=0)

    async def delete(self, q: str, *, filters: dict = None) -> DeleteResult:
        if q in self.users:
            del self.users[q]
            return DeleteResult(affected_records=1)
        return DeleteResult(affected_records=0)

# Define a service
class CreateUserService(Service[CreateResult]):
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self) -> CreateResult:
        user = User(username="john_doe", email="john@example.com")
        return asyncio.run(self.repository.create(user))

# Execute the service
executor = ServiceExecutor()
repository = InMemoryUserRepository()
service = CreateUserService(repository)
result = asyncio.run(executor.execute(CreateUserService, repository))
logger.info(f"User created with UID: {result.uid}")
```

## Modules

### Logging

Architecture's logging module is built on top of [Loguru](https://github.com/Delgan/loguru) and [Rich](https://github.com/willmcgugan/rich) to provide enhanced logging capabilities with colorful and structured output.

**Configuration:**

```python
from architecture.logging import logger

logger.debug("Debug message")
logger.info("Info message")
logger.success("Success message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Data

The data module handles data schemas, models, repositories, and results. It leverages `msgspec` for fast serialization and provides base classes to ensure consistency across data operations.

- **Schemas**: Define your data models by extending `BaseModel`.
- **Repositories**: Abstract interfaces for data access operations.
- **Results**: Standardized response classes for CRUD operations.

**Example:**

```python
from architecture import BaseModel

class Product(BaseModel):
    id: int
    name: str
    price: float
```

### Services

The services module provides base classes for defining business logic encapsulation. It supports both synchronous and asynchronous services with decorators to manage setup procedures.

- **Service**: Base class for synchronous services.
- **AsyncService**: Base class for asynchronous services.
- **ServiceExecutor**: Executes services, handling both sync and async seamlessly.

**Example:**

```python
from architecture.services import Service

class CalculateTaxService(Service[float]):
    def __init__(self, amount: float):
        self.amount = amount

    def execute(self) -> float:
        return self.amount * 0.2
```

### Utils

Architecture's utils module offers a variety of utility functions and decorators to aid in common development tasks, such as caching, file handling, and dynamic instance creation.

- **Decorators**: Enhance functions with caching (`pure`) and deprecation (`deprecated`).
- **Builders**: Simplify the construction of complex objects like `DynamicDict`.
- **Context Decorators**: Manage resources with context managers like `TempFile`.
- **Creators**: Utilities like `DynamicInstanceCreator` for dynamic class instantiation.

**Example:**

```python
from architecture.utils.decorators import pure

@pure(maxsize=256)
def compute_heavy(x, y):
    return x * y
```

## Deprecation Notice

⚠️ **Notice:** The `api` folder is **deprecated** and will be **removed in future versions** of Architecture. We recommend migrating any existing code that relies on the `api` module to the new structure provided by Architecture. Please refer to the [Migration Guide](#migration-guide) for detailed instructions.

## Migration Guide

### Migrating from Pydantic to Architecture's `BaseModel`

Architecture's `BaseModel` offers similar functionalities to Pydantic's `BaseModel`, providing fast serialization/deserialization and type validation. Migrating from Pydantic to Architecture's `BaseModel` is straightforward, but there are some considerations to keep in mind.

#### Steps to Migrate

1. **Update Imports:**

   Replace Pydantic imports with Architecture's `BaseModel`.

   ```python
   # From Pydantic
   from pydantic import BaseModel

   # To Architecture
   from architecture import BaseModel
   ```

2. **Update Model Definitions:**

   Change your model classes to inherit from architecture's `BaseModel`.

   ```python
   # Pydantic Model
   class User(BaseModel):
       username: str
       email: str

   # Architecture Model
   class User(BaseModel):
       username: str
       email: str
   ```

3. **Adjust Field Definitions:**

   Architecture's `BaseModel` uses `msgspec` under the hood. Ensure that field definitions are compatible. Most standard field definitions will work out of the box.

4. **Handle Validation and Configuration:**

   Some Pydantic features, such as the `Config` class for model configuration, may not be available in Architecture's `BaseModel`. Review your models for any Pydantic-specific configurations and adjust accordingly. The main goal here is to provide extremelly fast serialization, import time, application bloat.

   ```python
   # Pydantic
   class User(BaseModel):
       username: str
       email: str

       class Config:
           orm_mode = True
   ```

   ```python
   # Architecture - Configurations might need alternative handling
   class User(BaseModel):
       username: str
       email: str
   ```

#### Cautions

- **Missing Pydantic Features:**
  
  Architecture's `BaseModel` may not support all features available in Pydantic. Specifically, the `Config` attribute and some advanced validation mechanisms might be absent. Ensure that your application does not rely heavily on these features or find alternative implementations within Architecture.

- **Custom Validators:**
  
  If you use Pydantic's `@validator` decorators for custom validation, you'll need to implement equivalent validation logic in Architecture's models, possibly by overriding methods or using other utility functions provided by Architecture.

- **Third-Party Integrations:**
  
  Some third-party libraries that integrate tightly with Pydantic might not work seamlessly with Architecture's `BaseModel`. Test these integrations thoroughly after migration.

- **Performance Considerations:**
  
  While Architecture's `BaseModel` is optimized for performance, differences in serialization/deserialization behavior compared to Pydantic could impact your application's performance characteristics. Benchmark critical paths to ensure performance meets your requirements.

By following these steps and considerations, you can smoothly transition your models from Pydantic to Architecture's `BaseModel`, leveraging Architecture's optimized performance and integrated features while maintaining the integrity of your application's data models.

## Usage Examples

### Creating a Service

Services encapsulate business logic. Define a service by extending the `Service` or `AsyncService` base classes and implementing the `execute` method.

```python
from architecture.services import Service
from architecture import BaseModel

class Greeting(BaseModel):
    message: str

class GreetingService(Service[Greeting]):
    def __init__(self, name: str):
        self.name = name

    def execute(self) -> Greeting:
        return Greeting(message=f"Hello, {self.name}!")
```

### Defining a Repository

Repositories abstract data access logic. Implement repository interfaces to interact with your data sources.

```python
from architecture.data.repositories import Repository, CreateResult, ReadResult, ReadAllResult, UpdateResult, DeleteResult
from architecture import BaseModel

class Book(BaseModel):
    isbn: str
    title: str
    author: str

class BookRepository(Repository[Book]):
    async def create(self, entity: Book, *, filters: dict = None) -> CreateResult:
        # Implementation here
        pass

    async def read(self, q: str, *, filters: dict = None) -> ReadResult[Book]:
        # Implementation here
        pass

    async def read_all(self, *, filters: dict = None) -> ReadAllResult[Book]:
        # Implementation here
        pass

    async def update(self, q: str, entity: Book, *, filters: dict = None) -> UpdateResult:
        # Implementation here
        pass

    async def delete(self, q: str, *, filters: dict = None) -> DeleteResult:
        # Implementation here
        pass
```

### Using the Logging Module

Configure and use the logging module to track events within your application.

```python
from architecture.logging import logger

def process_data(data):
    logger.debug("Processing data: {}", data)
    # Processing logic
    logger.info("Data processed successfully.")

try:
    process_data("Sample Data")
except Exception as e:
    logger.error("An error occurred: {}", e)
```

## Contributing

We welcome contributions to Architecture! If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Write your changes and ensure they pass existing tests.
4. Submit a pull request with a detailed description of your changes.

Please adhere to the [code of conduct](CODE_OF_CONDUCT.md) and ensure your contributions maintain the quality and integrity of the project.

## License

Architecture is released under the [MIT License](LICENSE).

---

*Happy Coding with Architecture! 🚀*