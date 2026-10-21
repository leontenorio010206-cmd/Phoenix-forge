# Componentes y licencias de terceros · PhœnixForge 1.7.0

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
| Digital v0.31 de Helmut Neemann | Simulador externo GPLv3 descargable **opcionalmente** desde su ZIP oficial; no está incluido por defecto en el núcleo de PhœnixForge; https://github.com/hneemann/Digital | 
| Eclipse Temurin JRE 21 | Java opcional instalado desde paquete oficial verificado; condiciones OpenJDK GPLv2 con Classpath Exception y avisos del proveedor | 
| GTKWave | Visor externo opcional; no se incluye en el Setup principal |

`vendor/lock.json` identifica Icarus y su hash. `vendor/qt-sources.json` fija fuentes Qt/PySide y hashes publicados. `tools/prepare_qt_sources.py` obtiene y verifica esas fuentes **en construcción**, nunca en el primer arranque. `collect_licenses.py` conserva metadatos del paquete e intérprete y avisos originales; `stage_icarus.py` conserva dependencias y licencias. Los archivos descargados no se alteran.

El `.spec` limita los plugins y módulos Qt a los necesarios para esta aplicación raster. Si un nuevo DLL Qt aparece, detiene la construcción para revisar fuentes y licencias. La copia de fuentes/avisos puede exportarse desde **Ayuda → Exportar licencias y fuentes de componentes**. Icarus se incluye con el código exacto utilizado para compilarlo. El código completo y scripts de PhœnixForge permiten volver a combinar y empaquetar la aplicación con Qt modificado; no se prohíbe ingeniería inversa para depurar tales modificaciones.

Los metadatos y fuentes de las dependencias no bastan por sí solos para verificar un ejecutable. La **v1.7.0** se sometió a aceptación nativa automatizada de Windows; véanse el registro de GitHub Actions y el informe de compilación del artefacto concreto. Esto no certifica todas las configuraciones físicas ni reemplaza la revisión jurídica específica de licencias. La entrega de fuentes y avisos debe permanecer accesible junto a cualquier versión redistribuida.

Referencias originales: https://docs.python.org/3.11/license.html · https://doc.qt.io/qt-6/lgpl.html · https://doc.qt.io/qtforpython-6/licenses.html · https://pyinstaller.org/en/stable/license.html · https://github.com/steveicarus/iverilog/tree/v12_0 · https://nsis.sourceforge.io/License

Los PDFs originales del usuario no se redistribuyen. Los enlaces de fabricantes permanecen en el catálogo y en `docs/SOURCES.md`.

## Integración independiente con Digital

Gracias a **Helmut Neemann** por crear el simulador libre [Digital](https://github.com/hneemann/Digital) bajo **GNU GPLv3**. PhœnixForge no integra ni relicencia sus fuentes: prepara un componente externo Verilog y ofrece descargar la distribución oficial de Digital en un paso opcional y verificado. Digital sigue siendo un producto separado; no se implica colaboración, aval ni patrocinio de su autor. Consulte [LEGAL.md](LEGAL.md) y [CREDITS.md](CREDITS.md).
