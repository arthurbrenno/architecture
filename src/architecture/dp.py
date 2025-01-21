"""
Comprehensive type-safe design pattern markers with configurable documentation
"""

from typing import Callable, ClassVar


class MarkerRegistry:
    """Central registry for design pattern tracking"""

    _registry: ClassVar[dict[str, set[type]]] = {}

    @classmethod
    def register(cls, marker: str, target: type) -> None:
        """Register a class with a pattern marker"""
        cls._registry.setdefault(marker, set()).add(target)

    @classmethod
    def get_metrics(cls) -> dict[str, int]:
        """Get counts of pattern usage"""
        return {k: len(v) for k, v in cls._registry.items()}

    @classmethod
    def clear(cls) -> None:
        """Clear registry (mainly for testing)"""
        cls._registry.clear()


def design_pattern[T](
    marker_name: str,
    responsibility: str,
    use_cases: str = "Various application scenarios",
) -> Callable[[type[T]], type[T]]:
    """Factory for creating pattern marker decorators"""

    def decorator(cls: type[T]) -> type[T]:
        MarkerRegistry.register(marker_name, cls)
        return cls

    decorator.__name__ = marker_name
    decorator.__doc__ = f"""Design Pattern: {marker_name}
    
    * Responsibility: {responsibility}
    * Typical Use Cases: {use_cases}
    """
    return decorator


# =====================================================================
# Gang of Four Design Patterns
# =====================================================================

# Creational Patterns
AbstractFactory = design_pattern(
    "AbstractFactory",
    "Provide interface for creating families of related/dependent objects",
    "GUI toolkits, cross-platform device abstractions",
)

Builder = design_pattern(
    "Builder",
    "Separate object construction from its representation",
    "Complex object creation, step-by-step construction",
)

FactoryMethod = design_pattern(
    "FactoryMethod",
    "Defer object creation to subclasses",
    "Dependency injection, plugin systems",
)

Prototype = design_pattern(
    "Prototype",
    "Create objects by cloning existing instances",
    "Object caching, dynamic configuration",
)

Singleton = design_pattern(
    "Singleton",
    "Ensure single instance with global access",
    "Database connections, configuration managers",
)

# Structural Patterns
Adapter = design_pattern(
    "Adapter",
    "Convert interface to client-compatible form",
    "Legacy integration, third-party wrappers",
)

Bridge = design_pattern(
    "Bridge",
    "Decouple abstraction from implementation",
    "Driver architectures, platform-independent APIs",
)

Composite = design_pattern(
    "Composite",
    "Treat individual and composite objects uniformly",
    "GUI components, file systems",
)

Decorator = design_pattern(
    "Decorator",
    "Add responsibilities dynamically",
    "Middleware pipelines, feature toggling",
)

Facade = design_pattern(
    "Facade",
    "Provide unified interface to subsystems",
    "API gateways, library frontends",
)

Flyweight = design_pattern(
    "Flyweight",
    "Minimize memory usage through sharing",
    "Character rendering, particle systems",
)

Proxy = design_pattern(
    "Proxy", "Control access to original object", "Lazy loading, access control"
)

# Behavioral Patterns
ChainOfResponsibility = design_pattern(
    "ChainOfResponsibility",
    "Pass requests through handler chain",
    "Event filtering, middleware stacks",
)

Command = design_pattern(
    "Command", "Encapsulate requests as objects", "Undo/redo systems, macro recording"
)

Interpreter = design_pattern(
    "Interpreter", "Implement domain-specific language", "Query languages, rule engines"
)

Iterator = design_pattern(
    "Iterator",
    "Sequentially access collection elements",
    "Custom data structure traversal",
)

Mediator = design_pattern(
    "Mediator",
    "Centralize complex communications",
    "Chat systems, UI component coordination",
)

Memento = design_pattern(
    "Memento", "Capture/restore object state", "Snapshot systems, undo mechanisms"
)

Observer = design_pattern(
    "Observer",
    "Notify dependents of state changes",
    "Stock market systems, reactive UIs",
)

State = design_pattern(
    "State", "Change behavior with internal state", "Workflow engines, UI modes"
)

Strategy = design_pattern(
    "Strategy",
    "Encapsulate interchangeable algorithms",
    "Payment processors, AI behaviors",
)

TemplateMethod = design_pattern(
    "TemplateMethod", "Define algorithm skeleton with hooks", "Framework base classes"
)

Visitor = design_pattern(
    "Visitor",
    "Add operations without changing classes",
    "AST manipulation, document processing",
)

# =====================================================================
# Modern/Additional Patterns
# =====================================================================

Repository = design_pattern(
    "Repository",
    "Mediate between domain and data mapping",
    "Database abstraction layers",
)

UnitOfWork = design_pattern(
    "UnitOfWork",
    "Maintain atomic transaction operations",
    "Database transaction management",
)

NullObject = design_pattern(
    "NullObject",
    "Provide default behavior for missing objects",
    "Optional dependencies, stub implementations",
)

PublisherSubscriber = design_pattern(
    "PublisherSubscriber",
    "Decouple event sources from consumers",
    "Message queues, event buses",
)

DependencyInjection = design_pattern(
    "DependencyInjection",
    "Externalize dependencies creation",
    "Testing frameworks, modular systems",
)

ServiceLocator = design_pattern(
    "ServiceLocator",
    "Central registry for service access",
    "Plugin architectures, runtime service discovery",
)

Specification = design_pattern(
    "Specification", "Encapsulate business rules", "Validation engines, query builders"
)
