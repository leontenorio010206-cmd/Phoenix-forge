# Estado de la distribución — v1.1.0

**Proyecto fuente preparado para compilación de Windows.** Esta revisión integra una corrección del filtro de DLL de Qt que bloqueaba PyInstaller al encontrar `Qt6Network.dll`. Esta corrección no valida por sí misma el arranque final ni los motores HDL.

## Resultados conocidos

- Ejecutadas en un entorno Linux con Python 3.13: **58 pruebas superadas; 8 omitidas** porque faltan PySide6, Icarus o un `.exe` de Windows.
- Históricamente se consiguió abrir una versión local del programa y usar el simulador interno de semáforos en Windows 10.
- La simulación HDL desde un `.exe` local mostró errores de rutas y requiere una validación específica antes de anunciarse como funcional.
- No se ha validado Windows 7 ni la programación física de FPGA.

## Etiquetado de artefactos

- `PhoenixForge_v1.1.0_Portable.exe`: se publica como verificado por CI solo si las pruebas del proyecto y la aceptación nativa de Windows terminan correctamente.
- `PhoenixForge_v1.1.0_Portable_EXPERIMENTAL.exe`: puede generarse si la suite falla; **no está verificado** y puede tener funciones rotas.
- Los hashes SHA-256 acreditan integridad respecto del archivo descargado; no sustituyen firma de código ni pruebas en equipos reales.

Para errores reproducibles, adjunta los informes `windows-build-report.json` y `windows-tests.xml` publicados en Actions.
