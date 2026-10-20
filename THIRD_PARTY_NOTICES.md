# Componentes y licencias de terceros · 1.1

El código propio y el fénix original son MIT (`LICENSE`). Los nombres de FPGA son referencias informativas, sin patrocinio. Las licencias de terceros no se sustituyen por MIT.

| Componente | Uso y condición |
|---|---|
| Python 3.11.9 | Intérprete empaquetado; licencia PSF y avisos originales copiados del intérprete Windows |
| PySide6 / Shiboken6 6.8.3 | Bindings Qt; términos LGPLv3/GPLv3 según archivo; fuentes correspondientes incluidas al construir |
| Qt 6.8.3 Core, Gui, Widgets, Svg | Bibliotecas dinámicas; fuentes QtBase/QtSvg y avisos propios/de terceros incluidos al construir |
| Icarus Verilog 12.0 | Compilador y runtime como procesos separados; GPL-2.0-or-later, COPYING y fuente exacta v12_0 incluida |
| MinGW runtime | Dependencias resueltas de la construcción real; licencias originales copiadas de los paquetes MSYS2. GCC runtime tiene su excepción de biblioteca; los demás componentes conservan sus términos |
| PyInstaller 6.22.3 | Bootloader/empaquetado; GPL con excepción de distribución para aplicaciones; avisos de su paquete |
| NSIS 3.11 | Generador de instalador; licencia zlib/libpng para el núcleo, véase documentación oficial |
| PySide2 / Qt5 | Solo perfil de construcción heredado experimental; no se mezcla en el portable moderno |
| GTKWave / Digital | Herramientas externas opcionales, no redistribuidas como parte del programa |

`vendor/lock.json` identifica Icarus y su hash. `vendor/qt-sources.json` fija fuentes Qt/PySide y hashes publicados. `tools/prepare_qt_sources.py` obtiene y verifica esas fuentes **en construcción**, nunca en el primer arranque. `collect_licenses.py` conserva metadatos del paquete e intérprete y avisos originales; `stage_icarus.py` conserva dependencias y licencias. Los archivos descargados no se alteran.

El `.spec` limita los plugins y módulos Qt a los necesarios para esta aplicación raster. Si un nuevo DLL Qt aparece, detiene la construcción para revisar fuentes y licencias. La copia de fuentes/avisos puede exportarse desde **Ayuda → Exportar licencias y fuentes de componentes**. Icarus se incluye con el código exacto utilizado para compilarlo. El código completo y scripts de PhœnixForge permiten volver a combinar y empaquetar la aplicación con Qt modificado; no se prohíbe ingeniería inversa para depurar tales modificaciones.

Los metadatos y fuentes de las dependencias no son una prueba de que se haya construido el EXE: consulte el informe de entrega. En la entrega de fuentes solo están presentes las dependencias efectivamente preparadas. La revisión de dependencias PE y la aceptación final Windows siguen pendientes.

Referencias originales: https://docs.python.org/3.11/license.html · https://doc.qt.io/qt-6/lgpl.html · https://doc.qt.io/qtforpython-6/licenses.html · https://pyinstaller.org/en/stable/license.html · https://github.com/steveicarus/iverilog/tree/v12_0 · https://nsis.sourceforge.io/License

Los PDFs originales del usuario no se redistribuyen. Los enlaces de fabricantes permanecen en el catálogo y en `docs/SOURCES.md`.
