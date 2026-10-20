from app.plugins.sdk import Plugin
from app.core.hdl import modules


class Inventory(Plugin):
    def activate(self, context):
        context.register("hdl_tool", "inventory", self.run)

    def run(self, project):
        return modules(project.files)


def create_plugin():
    return Inventory()

