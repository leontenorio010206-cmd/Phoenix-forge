# Manual de desarrollo · PhœnixForge 1.1.0

## Entornos

Conserve entornos separados. El objetivo Windows moderno fija Python 3.11.9 x64 y PySide6 6.8.3. Las pruebas locales de esta actualización usan Python 3.12.14/Qt 6.8.3 en Linux. El código de aplicación mantiene sintaxis Python 3.8; esto no demuestra compatibilidad nativa Windows 7.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate; POSIX: source .venv/bin/activate
python -m pip install -r requirements/modern.txt -r requirements/test-modern.txt
python -m app
python -m pytest -q
```

Desde fuentes se requiere Icarus para pruebas HDL reales. `pytest` muestra omisiones explícitas si falta. No convierta una omisión en verificación. El perfil legacy utiliza los archivos de requisitos `legacy` y no se mezcla con PySide6.

## Límites entre módulos

| Directorio | Responsabilidad |
|---|---|
| `app/core` | Proyecto, esquema, índice HDL, contratos y factorías |
| `app/editors` | Editor Qt, resaltado, líneas y búsqueda |
| `app/simulators` | Quine–McCluskey, modelos internos, Icarus y VCD |
| `app/devices` | Catálogo JSON validado; no controladores JTAG |
| `app/exporters` | Paquete interoperable y componentes/licencias |
| `app/plugins` | API 1, descubrimiento, confianza y ciclo de vida |
| `app/ui` | Vistas, acciones y trabajador de simulación |
| `app/utils` | Recursos, datos persistentes y adaptador de procesos |
| `tools` | Construcción, preparación de dependencias y aceptación |
| `installer` | Instalador NSIS y desinstalador por usuario |

El núcleo no importa Qt. `app/ui/qt.py` concentra bindings y `app/utils/platform.py` opciones de procesos Windows/POSIX. La UI comparte factorías y motores con la suite. Los modelos internos no interpretan HDL; sus trazas no validan lo editado.

## Recursos y vida de los datos

`resource_root()` usa `_MEIPASS` únicamente en la aplicación congelada y la raíz del proyecto desde fuentes. Assets, perfiles, ejemplos, documentos, compilador y fuentes de terceros son recursos de lectura. `data_dir()` resuelve `%LOCALAPPDATA%\PhoenixForge` en Windows o XDG en POSIX; `PHOENIXFORGE_DATA` permite una ubicación de desarrollo/prueba explícita.

Proyectos, ajustes, logs y `runs/<project_id>/<run_id>` nunca se guardan por defecto dentro de `_MEIPASS`. `user_projects_dir()` propone una carpeta persistente. Cambiar el EXE o desinstalar no borra esa carpeta.

Icarus incluido se resuelve como `vendor/icarus/bin/iverilog.exe` y `vvp.exe`; `-B` apunta a `lib/ivl`, `-M` a módulos VPI. El proceso hijo recibe `vendor/icarus/bin` en su entorno para DLLs. No se altera el PATH global. Las rutas avanzadas elegidas por el usuario tienen precedencia.

## Simulación y estabilidad

`SimulationThread` toma una copia del proyecto. `IcarusEngine` escribe fuentes en una ejecución aislada, compila y luego ejecuta con listas de argumentos, `shell=False` y tiempo máximo. No hay resultados ficticios ni éxito tras un retorno no cero. La UI sigue procesando eventos y advierte si se editó después de tomar la copia.

La última traza exitosa y los logs del último intento se guardan por separado. `run.json` registra comandos y hashes para diagnóstico; las rutas que aparecen allí describen esa ejecución, no son rutas incrustadas en el código.

HDL puede realizar operaciones de archivos y un plugin autorizado tiene los permisos del proceso. Estos procesos no son una sandbox. La importación Python/C++ solo conserva texto. Los guardados y exportaciones rechazan rutas peligrosas y sobrescritura no autorizada.

## Extensiones

`LanguageAdapter`, `Simulator` y `Exporter` son contratos estables. El método base de conversión lanza `NotImplementedError`; VHDL/Python-HDL/C++-HLS no se convierten automáticamente.

Plugins API 1 pueden registrar dispositivos, simuladores, exportadores y herramientas; solo `hdl_tool` dispone de ejecución genérica ya conectada a la UI. Los demás requieren el adaptador de selección y presentación. Consulte `PLUGIN_SDK.md`. Descargar un plugin elimina registros y llama a `deactivate`, pero no revierte efectos arbitrarios ni detiene hilos que el propio plugin no gestione.

El parser de puertos es textual: no elabora parámetros/macros ni todo SystemVerilog. Los metadatos identifican los casos sin resolver. El compilador real decide la validez HDL.

## Verificación y mantenimiento

```sh
python -m pytest -q --junitxml=build/local-tests.xml
python tools/smoke_flow.py --offscreen --output build/verification
python tools/create_examples.py
python tools/package_release.py --output ../PhoenixForge_v1.1.0_Source.zip
```

`app/acceptance.py` se usa tanto desde fuentes como mediante `EXE --self-test CARPETA --require-bundled`. La aceptación abre ventanas, edita, simula con Icarus, comprueba VCD, guarda/reabre y carga/descarga el plugin incluido conocido. Solo el arnés contesta diálogos automáticamente. El código normal solicita confianza al usuario.

`tools/test_packaged.py` exige Windows nativo, inspecciona el PE x64 GUI y tamaño, arranca normalmente sin argumentos, comprueba una ventana mediante Win32 y la cierra. Ejecuta dos flujos integrales con PATH reducido y directorios con espacios/acentos. Esto no sustituye la prueba final en una VM limpia sin herramientas de desarrollo.

Versiones de producto, esquema de proyecto y API de plugin son independientes. 1.1 no cambia esquema 1 ni API 1. La regresión abre proyectos con `app_version=1.0.0` y conserva todos los campos. Para cambios futuros implemente migraciones secuenciales y nunca reescriba silenciosamente el original.

Actualice juntos `VERSION`, `app/__init__.py`, `pyproject.toml`, metadatos Windows, nombre de artefactos y changelog. No añada caches, entornos ni binarios de trabajo a Git. La etiqueta local `v1.0.0` conserva la base original; la actualización se registra en un commit separado. No hay remoto publicado.

## Distribución y modificación de Qt

Siga `BUILD_WINDOWS.md`. La construcción nativa falla explícitamente en otros sistemas. Los fuentes correspondientes de Icarus y de los módulos Qt utilizados se conservan junto con sus avisos, y son exportables desde Ayuda. El código MIT de la aplicación, los `.spec` y los scripts permiten reconstruir el programa con bibliotecas modificadas; no se imponen verificaciones de firma ni restricciones de ingeniería inversa para depurar esas modificaciones.

Para sustituir Qt/PySide, construya las versiones modificadas según los archivos README/CMake de sus fuentes, instálelas en el entorno de construcción y reconstruya con PyInstaller. Los pins definen la edición reproducible oficial; para una edición modificada ajuste explícitamente los pins y los hashes/fuentes, registre el cambio y repita la aceptación. La lista permitida de DLLs Qt del `.spec` obliga a revisar fuentes y licencias si se añade un módulo.

El empaquetado no es bit a bit reproducible entre cualquier equipo: Python/Qt/Icarus están fijados, pero MSYS2 es un repositorio evolutivo. El workflow conserva inventarios Python/MSYS2 y hashes de salida. Para reproducibilidad binaria estricta se necesita además congelar el repositorio MSYS2 y la imagen del runner.

## Historia Git incluida

El ZIP de fuentes incluye `history/PhoenixForge.git.bundle` con la base importada y el commit de actualización, sin remoto ni credenciales. Para restaurarla en otra carpeta: `git clone history/PhoenixForge.git.bundle PhoenixForge-dev`. La historia conserva la versión original; el checkout de 1.1 contiene el refactor. Las fuentes y avisos Qt descargados no están en Git; se incluyen aparte en el ZIP y se pueden copiar, o recuperar mediante el script de preparación verificada.
