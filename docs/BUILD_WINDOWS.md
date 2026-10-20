# Construcción Windows · 1.1.0

**Este procedimiento está preparado; la construcción nativa aún no se ha ejecutado.** Un error aborta la entrega y queda registrado. Los EXE no se sustituyen por archivos de otro tipo. Solo se usan estas herramientas en el equipo de construcción, nunca en el equipo del usuario final.

## Mediante runner privado

1. En un repositorio **privado autorizado**, copie el árbol completo con `.github/workflows/windows-release.yml`. No publique una release. El workflow también comprueba `repository.private`.
2. Ejecute **Private Windows distribution** por `workflow_dispatch` o mediante un push a una rama `build/...`. El runner `windows-2022` es Windows Server 2022 x64; conserve esa identidad en el informe.
3. El workflow instala Python 3.11.9, requisitos fijados, MSYS2 MINGW64 y NSIS 3.11; construye Icarus desde la fuente incluida; resuelve y copia DLLs PE x64 y sus licencias; prepara fuentes Qt con hashes.
4. Ejecuta regresión de código, PyInstaller GUI onefile, validación de tamaño/arquitectura/hash, arranque normal y dos flujos de aceptación nativa con motor incluido. Solo después construye Setup.
5. Descargue el artefacto privado `PhoenixForge-v1.1.0-windows-x64`, retención 7 días. Contiene los dos EXE si ambos se generaron, ZIP de fuentes, SHA-256 e informe. Los diagnósticos se guardan aun cuando el job falla.
6. Complete la prueba en Windows 10 limpio de `COMPATIBILITY.md`. Un éxito del runner no demuestra una VM Windows 10 sin dependencias.

El job no crea un repositorio, no publica contenido y no solicita secretos de distribución. Permisos de contenido: lectura. Los actions se identifican por su versión mayor; MSYS2 y la imagen hospedada cambian con el tiempo. Los inventarios guardados permiten identificar el entorno, pero no garantizan compilaciones bit a bit idénticas.

## Construcción local equivalente

En Windows x64 con Python 3.11.9, instale el entorno de desarrollo:

```bat
install_windows.bat modern
.venv-modern\Scripts\python.exe -m pip install -r requirements\build-modern.txt -r requirements\test-modern.txt
```

Instale MSYS2 para el equipo de construcción y abra su terminal **MINGW64**. En ella:

```sh
pacman -Syu
pacman -S --needed make autoconf automake bison flex gperf mingw-w64-x86_64-gcc
cd /ruta/al/PhoenixForge
bash tools/build_icarus_msys2.sh
```

Se comprueba el hash antes de extraer la fuente Icarus; se desactivan readline/history y se usa libgcc/libstdc++ estática. No se requiere un shell MSYS en la distribución. `build/icarus-prefix.txt`, `mingw-bin.txt` y `mingw-licenses.txt` registran las rutas de preparación de esta ejecución.

En PowerShell del equipo de construcción:

```powershell
$pfPrefix = (Get-Content build/icarus-prefix.txt -Raw).Trim()
$pfBin = (Get-Content build/mingw-bin.txt -Raw).Trim()
$pfLicenses = (Get-Content build/mingw-licenses.txt -Raw).Trim()
.venv-modern\Scripts\python.exe tools/stage_icarus.py --prefix $pfPrefix --dependency-bin $pfBin --license-dir $pfLicenses
```

`stage_icarus.py` requiere un destino `vendor/icarus` nuevo: no combina versiones de compiladores. Para repetir, use otro checkout limpio o retire únicamente la preparación anterior después de conservar sus informes.

Instale NSIS **3.11** en el equipo de construcción y ejecute `build_windows.bat modern`. Este descarga/verifica las fuentes Qt necesarias y llama a `tools/build_windows.py`. Una alternativa explícita es:

```bat
.venv-modern\Scripts\python.exe tools\prepare_qt_sources.py
.venv-modern\Scripts\python.exe tools\build_windows.py --makensis "C:\Program Files (x86)\NSIS\makensis.exe"
```

La primera orden descarga solo entradas de construcción. La segunda exige que ya existan fuentes y runtime, comprueba licencias y ejecuta la construcción real. `--portable-only` permite depurar el portable sin producir instalador; no satisface los tres entregables del pedido.

## Resultados y controles

- `dist/PhoenixForge_v1.1.0_Portable.exe`: PE AMD64, subsistema GUI, al menos 20 MiB; ese umbral detecta un artefacto truncado, no demuestra funcionalidad.
- `dist/PhoenixForge_v1.1.0_Setup.exe`: instalador NSIS gráfico; su cargador puede ser PE x86, el payload es x64. Se valida como instalador, no como portable x64.
- `build/windows-build-report.json`: host exacto, pruebas, errores y hashes de artefactos.
- `build/packaged-acceptance/`: arranque ordinario, dos ejecuciones, capturas, VCD, proyectos y reportes. El PATH del hijo contiene solo Windows/System32, además del runtime que añade la propia app a Icarus.
- `dist/SHA256SUMS.txt`: hashes de EXE realmente generados. El ZIP produce su propio `.sha256`.

`tools/test_packaged.py EXE --output CARPETA` repite la aceptación. También puede establecer `PHOENIXFORGE_EXE` y ejecutar `pytest -m packaged`. Se rechaza Wine como prueba nativa. La ausencia del EXE produce omisión explícita en pytest, no aprobación.

Para probar sin Python en la VM limpia, abra el EXE normalmente y use el procedimiento manual; el propio EXE también admite `--self-test CARPETA --require-bundled` desde un acceso directo de prueba.

## Instalador y datos

NSIS usa `RequestExecutionLevel user`, menú Inicio del usuario y directorio predeterminado `%LOCALAPPDATA%\Programs\PhoenixForge`. La selección de acceso directo de escritorio es opcional. No modifica PATH ni descarga dependencias. El desinstalador elimina los archivos de la instalación; deja `%LOCALAPPDATA%\PhoenixForge` y los proyectos personales.

El portable extrae recursos con el mecanismo normal de PyInstaller y necesita un TEMP escribible. No configura una ruta temporal compartida fija ni se eleva a administrador. Los ajustes y resultados se resuelven fuera de esa extracción. Los EXE preparados carecen de certificado de firma de código; un SHA-256 es integridad, no firma Authenticode.

## Licencias y fuentes

Se entregan el archivo exacto Icarus v12_0 y los scripts usados para compilarlo. Las fuentes QtBase/QtSvg/QtImageFormats y PySide/Shiboken 6.8.3 se obtienen con hashes fijos y se incluyen en recursos exportables. Los avisos se copian, no se reescriben. El `.spec` rechaza módulos Qt no contemplados.

Si cambian módulos, DLLs, versiones o flags, actualice la procedencia y el conjunto de fuentes, revise licencias y repita aceptación. No reutilice un informe de una compilación anterior.
