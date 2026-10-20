# Formato .pforge — esquema 1

Un proyecto es un ZIP sin cifrar. `manifest.json` está en la raíz; los textos UTF-8 están bajo `src/` y los resultados binarios bajo `results/`. No es un formato ejecutable ni un mecanismo de firma digital.

El manifiesto contiene:

| Campo | Tipo / significado |
|---|---|
| `format` | Cadena exacta `PhoenixForge` |
| `schema_version` | Entero 1; diferente de la versión comercial |
| `app_version` | Versión de la aplicación que lo escribió |
| `project_id` | UUID, también usado para separar ejecuciones |
| `name` | Nombre no vacío, hasta 200 caracteres |
| `device` | ID de perfil; los desconocidos se conservan al abrir |
| `hdl_files` | Lista de objetos `{path, sha256}` bajo `src/` |
| `artifacts` | Lista equivalente bajo `results/` |
| `simulation` | Objeto; `top`, `testbench`, `timeout` y parámetros de laboratorio |
| `pins` | Objeto de puerto a pin, ambos cadenas |
| `metadata` | Objeto JSON de datos del usuario / procedencia |
| `export_state` | Objeto JSON de historial informativo de exportación |

Ejemplo mínimo de estructura conceptual:

```json
{
  "format": "PhoenixForge",
  "schema_version": 1,
  "app_version": "1.1.0",
  "project_id": "00000000-0000-4000-8000-000000000001",
  "name": "Mi diseño",
  "device": "ep2c5t144c8n",
  "hdl_files": [],
  "artifacts": [],
  "simulation": {"top": "", "testbench": "", "timeout": 15},
  "pins": {},
  "metadata": {},
  "export_state": {}
}
```

Los proyectos reales generan SHA-256 sobre los bytes exactos de cada archivo. Todos los miembros del ZIP deben estar declarados; el manifiesto no se lista a sí mismo. El guardado escribe primero un archivo temporal. Al reemplazar una copia autorizada usa `os.replace`; al crear usa publicación mediante enlace o copia exclusiva si el sistema no admite enlaces.

## Validación

- Máximo 512 archivos de contenido y 32 MiB descomprimidos; manifiesto máximo 1 MiB.
- Prohibidos directorios explícitos, enlaces simbólicos, archivos cifrados y miembros duplicados.
- Rutas POSIX relativas; se rechazan `..`, barras invertidas, unidades, nombres reservados de Windows, separadores redundantes y caracteres no portátiles.
- Se rechazan colisiones por mayúsculas/minúsculas y una ruta que sea a la vez archivo y directorio.
- No se llama a `extractall`: se leen los miembros después de validar. La escritura de fuentes usa destinos confinados y comprueba enlaces del destino.
- JSON con claves duplicadas, fuentes que no sean UTF-8, hashes incorrectos o miembros no declarados generan un error.

Los hashes detectan corrupción, no autenticidad: alguien que controle el contenedor puede cambiar los archivos y recalcularlos. No abras o ejecutes código por considerar que un hash válido acredita su origen.

## API y migración

`Project.open(path)` valida y carga; `Project.save(path, overwrite=False)` no sustituye un archivo existente sin autorización del llamador. La interfaz confirma explícitamente las sustituciones. `Project.import_file(...)` incorpora fuentes sin ejecutarlas. `write_sources(directory)` se usa sobre carpetas de trabajo nuevas.

Existe una migración del esquema de desarrollo 0 al 1: añade `export_state`, `artifacts`, `pins` y `metadata` si faltan, y registra `metadata.migrated_from=0`. Los demás campos y los hashes siguen siendo obligatorios. No representa soporte para un producto anterior publicado. Se rechazan versiones futuras en vez de interpretarlas parcialmente.

Al ampliar el formato, añade una migración secuencial, fixtures y pruebas de ida y vuelta. No reutilices un número de esquema para un cambio incompatible. Los `.pforge` no contienen contraseñas ni preferencias globales de ejecutables.


## Continuidad 1.0 → 1.1

Ambas versiones usan el esquema 1. Abrir un proyecto de 1.0 no elimina fuentes, artefactos, pines, metadatos ni estado de exportación. El siguiente guardado actualiza solamente la versión escritora y los contenidos modificados por el usuario. No se limpia automáticamente el contenido de proyectos anteriores. La prueba `test_version_100_project_preserves_data` comprueba esta continuidad.
