"""Stable extension points. Unimplemented language conversions are explicit."""
from abc import ABC, abstractmethod


class LanguageAdapter(ABC):
    language = "unknown"

    @abstractmethod
    def discover_modules(self, sources):
        """Return module metadata. Never execute imported sources."""

    def lower_to_verilog(self, sources):
        raise NotImplementedError("Conversión HDL/HLS no implementada para " + self.language)


class Simulator(ABC):
    @abstractmethod
    def run(self, project, **options):
        """Return a result carrying success, diagnostics and output artifacts."""


class Exporter(ABC):
    @abstractmethod
    def export(self, project, destination):
        """Write a checked export, raising on failure."""

