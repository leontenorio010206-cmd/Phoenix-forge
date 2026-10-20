# Fuentes técnicas

Consultadas durante el desarrollo de esta entrega, 9–10 de octubre de 2026. Las versiones son decisiones fijadas para reproducibilidad, no promesas de soporte futuro de terceros.

## Material proporcionado por el usuario

- **Práctica 6.0.pdf**: cálculos de reloj y contadores, identificación del EP2C5T144C8N y ejercicio del semáforo, páginas 12–25. Los errores de anchos y unidades se corrigen explícitamente en `ACADEMIC_NOTES.md`.
- **Tutorial Verilog..pdf**: módulos, puertos, lógica combinacional, procesos y testbenches. Las tareas de formas de onda se adaptan a VCD/Icarus.

## Python, Qt y empaquetado

- [Python 3.11: uso en Windows](https://docs.python.org/3.11/using/windows.html): soporte Windows 8.1+, referencia a Python 3.8 para Windows 7.
- [Python 3.11.9](https://www.python.org/downloads/release/python-3119/): instaladores oficiales de la base moderna elegida.
- [Python 3.8.10](https://www.python.org/downloads/release/python-3810/): instaladores de la base heredada y estado de la rama.
- [Cambios Python 3.8](https://docs.python.org/3/whatsnew/3.8.html): restricción KB2533623 para Windows 7.
- [Plataformas Qt 6.8](https://doc.qt.io/qt-6.8/supported-platforms.html): Windows 10 1809 como mínimo del conjunto moderno.
- [Fuente oficial de la tabla Qt 5.15](https://raw.githubusercontent.com/qt/qtdoc/5.15/doc/src/platforms/supported-platforms.qdocinc): Windows 7 x86/x64 en esa rama histórica.
- [PySide2 5.15.2.1 en PyPI](https://pypi.org/project/PySide2/5.15.2.1/): versiones de intérprete y ruedas disponibles.
- [PyInstaller 4.10: requisitos](https://pyinstaller.org/en/v4.10/requirements.html): Windows 7 no soportado oficialmente, aunque puede funcionar.
- [PyInstaller 5.13.2: requisitos](https://pyinstaller.org/en/v5.13.2/requirements.html): Windows 8 o posterior.

## Herramientas HDL

- [Instalación oficial Icarus Verilog](https://steveicarus.github.io/iverilog/usage/installation.html).
- [Opciones de vvp](https://steveicarus.github.io/iverilog/usage/vvp_flags.html): `-N` evita interacción y convierte `$stop` en fallo.
- [Código Icarus](https://github.com/steveicarus/iverilog): motor real ejecutado como proceso; fuente exacta v12_0 incluida en vendor/sources.


## Dispositivos

- [Cyclone II Device Handbook](https://cdrdv2-public.intel.com/654376/cyc2_cii5v1.pdf): EP2C5, 4,608 LE y 119,808 bits de RAM. No se deducen pines de usuario a partir del número de terminales del encapsulado.
- [Cyclone IV Device Handbook](https://www.intel.com/content/www/us/en/content-details/653974/cyclone-iv-device-handbook.html).
- [Cyclone V](https://www.intel.com/content/www/us/en/products/details/fpga/cyclone/v.html).
- [AMD/Xilinx Spartan-6 DS160](https://docs.amd.com/v/u/en-US/ds160).
- [AMD/Xilinx serie 7 DS180](https://docs.amd.com/v/u/en-US/ds180_7Series_Overview).
- [Lattice iCE40](https://www.latticesemi.com/iCE40) y [UltraPlus](https://www.latticesemi.com/Products/FPGAandCPLD/iCE40UltraPlus).
- [Guía de selección Lattice, revisión 28](https://www.latticesemi.com/-/media/LatticeSemi/Documents/ProductBrochures/NZ/PSG_2020_I0211K_Rev28.ashx?document_id=9): recursos de HX1K y UP5K.
- [Lattice ECP5](https://www.latticesemi.com/Products/FPGAandCPLD/ECP5).
- [GOWIN LittleBee](https://www.gowinsemi.com/en/product/littlebee_fpga/).

Las familias generales no reciben cifras que dependan de chip, encapsulado o grado. Todos los perfiles conservan sus fuentes y separan simulación RTL de síntesis y programación física verificadas. No se realizó ninguna prueba sobre hardware FPGA.

## Distribución 1.1

- [PyInstaller 6.22.3](https://pyinstaller.org/en/stable/): exige compilar en Windows para generar Windows; opciones GUI/onefile.
- [MSYS2 setup action](https://github.com/msys2/setup-msys2): entorno MINGW64 para construir Icarus en un runner Windows.
- [Runner Windows 2022](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md): Windows Server 2022; no es una VM Windows 10 limpia.
- [NSIS 3.11](https://sourceforge.net/projects/nsis/files/NSIS%203/3.11/): compilador de instalador fijado.
- [Fuentes Qt 6.8.3](https://download.qt.io/archive/qt/6.8/6.8.3/submodules/) y [PySide/Shiboken](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.8.3-src/). `vendor/qt-sources.json` fija URLs y hashes publicados.
- [Icarus v12_0](https://github.com/steveicarus/iverilog/tree/v12_0), archivo completo verificado mediante `vendor/lock.json`. Se mantiene 12.0 por la regresión ejecutada, sin afirmar que sea la última versión.
- [LGPL y Qt](https://doc.qt.io/qt-6/lgpl.html) y [licencias Qt for Python](https://doc.qt.io/qtforpython-6/licenses.html): avisos y acceso a fuentes de los componentes incluidos.

Las referencias académicas y las cifras FPGA se conservan del trabajo 1.0; no se han cambiado ni se atribuyen nuevas pruebas físicas a esta actualización.
