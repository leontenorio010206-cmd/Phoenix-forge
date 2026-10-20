# SDK de plugins · API 1

Cada plugin es una carpeta con `plugin.json` y un punto de entrada Python relativo. Descubrir carpetas lee y valida los manifiestos; no importa código.

```json
{
  "id": "org.example.module_inventory",
  "name": "Inventario de módulos",
  "version": "1.0.0",
  "api_version": 1,
  "entry_point": "plugin.py"
}
```

El ID requiere un espacio de nombres y caracteres ASCII en minúscula. Se rechazan IDs duplicados, API desconocida, versiones inválidas, rutas inseguras, enlaces y archivos excesivos. El descubrimiento calcula una huella; si el código cambia, debe volver a descubrirse antes de cargarlo.

```python
from app.plugins.sdk import Plugin
from app.core.hdl import modules

class Inventory(Plugin):
    def activate(self, context):
        context.register("hdl_tool", "inventory", self.run)

    def run(self, project):
        return modules(project.files)

    def deactivate(self):
        pass

def create_plugin():
    return Inventory()
```

Puede copiar `examples/plugins/module_inventory` a la carpeta de plugins indicada en Configuración o seleccionar su carpeta padre desde el gestor. Seleccione el plugin y pulse Cargar; la advertencia explica que es código de terceros. Después se puede ejecutar su herramienta sobre el proyecto activo y descargarlo.

## Registro y ciclo de vida

`PluginContext.register(kind, name, value)` registra una contribución bajo `(kind, plugin_id + ':' + name)`. Los tipos admitidos son `device`, `simulator`, `exporter` y `hdl_tool`. No se permite reemplazar una contribución ya existente.

La factoría `create_plugin()` debe devolver una instancia de `Plugin`. Tras importar el módulo, el gestor llama `activate(context)`. Si falla, elimina sus contribuciones, registra el error e intenta desactivar la instancia. Al descargar, llama `deactivate()` y retira contribuciones y módulo incluso si hay errores.

Las herramientas `hdl_tool` son llamadas con el proyecto y devuelven un resultado representable como texto. Para tareas largas, el plugin debe gestionar su ejecución sin bloquear la UI. Los contratos base de simuladores y exportadores están en `core/contracts.py`; el catálogo de dispositivos define su esquema en `devices/catalog.py`.

**Alcance v1.0:** la UI invoca herramientas HDL genéricas. Las otras tres categorías tienen contratos y registro, pero todavía necesitan adaptadores de integración con la selección de motores, catálogo y menús de exportación. Registrarlas no las convierte automáticamente en funciones operativas de la ventana principal.

## Confianza y límites

La autorización no convierte el plugin en código aislado. Un módulo Python puede leer o modificar archivos, iniciar procesos y acceder a la red con los permisos del usuario. La descarga no puede revertir efectos externos arbitrarios. No instale código desconocido.

`deactivate()` debe cancelar trabajo propio, desconectar señales y cerrar archivos. La huella es una comprobación de cambios entre descubrimiento y carga, no una firma del autor. Cambiar la API exige incrementar `API_VERSION` y documentar la migración; la versión del plugin sigue SemVer.
