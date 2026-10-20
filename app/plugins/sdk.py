from abc import ABC, abstractmethod

API_VERSION = 1
KINDS = ("device", "simulator", "exporter", "hdl_tool")


class Plugin(ABC):
    @abstractmethod
    def activate(self, context):
        """Register contributions using context.register(kind, id, object)."""

    def deactivate(self):
        """Release resources and stop owned work before returning."""


class PluginContext:
    def __init__(self, owner, registry):
        self.owner, self.registry = owner, registry

    def register(self, kind, name, value):
        if kind not in KINDS or not isinstance(name, str) or not name:
            raise ValueError("Contribución inválida")
        key = (kind, self.owner + ":" + name)
        if key in self.registry:
            raise ValueError("Contribución duplicada")
        self.registry[key] = value

