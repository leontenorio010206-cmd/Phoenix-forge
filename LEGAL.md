# Avisos legales y distribución — PhœnixForge 1.7.0

Este documento explica la estructura de licencias del proyecto. **No constituye una certificación jurídica ni sustituye la revisión legal de la distribución específica.**

## Código original de PhœnixForge

El código creado específicamente para PhœnixForge se distribuye bajo **MIT**, conforme a [LICENSE](LICENSE). Copyright (c) 2026 **Leonardo Antonio Hernández Tenorio**.

La licencia MIT **no se aplica automáticamente a los componentes de terceros** ni cambia sus licencias, marcas o titulares de derechos. Los archivos de terceros conservan sus avisos.

## Digital de Helmut Neemann

- Proyecto oficial: https://github.com/hneemann/Digital
- Licencia declarada en su repositorio: **GNU GPL versión 3**.
- Integración: PhœnixForge genera archivos Verilog, prepara un runtime Icarus y **lanza una instancia independiente de Digital**. No se ha incorporado su código fuente directamente a PhœnixForge.
- Distribución opcional: el Setup ofrece **descargar**, previa selección explícita del usuario, el ZIP oficial **Digital v0.31**; verifica tamaño y SHA-256 antes de extraerlo en el directorio del usuario.
- El paquete principal de PhœnixForge **no incluye por defecto Digital.jar**. Cuando Digital se descarga, el usuario puede consultar los términos y el código fuente de su repositorio y la licencia incluida en su distribución oficial.
- No se deben redistribuir modificaciones de Digital sin cumplir las condiciones GPLv3 correspondientes. Tampoco se puede afirmar asociación o patrocinio por Digital.

## Otros componentes

| Software | Uso principal | Licencia o condiciones de referencia |
| --- | --- | --- |
| Icarus Verilog 12.0 | Compilador y simulador de Verilog, empaquetado en el EXE completo | **GPL-2.0-or-later**; conservar fuentes y avisos correspondientes |
| Qt / PySide6 / Shiboken6 6.8.3 | Biblioteca y bindings de interfaz gráfica | Licencias por módulo, incluidos términos **LGPLv3/GPLv3**; cumplir obligaciones sobre bibliotecas, avisos y fuentes |
| Python 3.11.9 | Intérprete | Licencia PSF y avisos incluidos |
| Eclipse Temurin JRE 21 | Runtime Java opcional, descargado desde Adoptium | OpenJDK GPLv2 con Classpath Exception y avisos correspondientes |
| PyInstaller | Construcción del ejecutable | Términos de su bootloader y excepciones de distribución |
| NSIS | Creación del Setup.exe | Sus términos de licencia y avisos |
| Arduino CLI / openFPGALoader | Herramientas externas de hardware cuando se instalen o seleccionen | Consultar las licencias vigentes de cada proyecto |

Ver [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [docs/ONLINE_SETUP.md](docs/ONLINE_SETUP.md) y los archivos de licencias/fuentes entregados con la construcción.

## Obligaciones prácticas antes de distribuir

1. Conservar los avisos de copyright y las licencias originales en binarios y fuentes.
2. Ofrecer el código fuente correspondiente de componentes copyleft según sus licencias y asegurar que las bibliotecas LGPL se puedan modificar/reemplazar conforme a sus condiciones.
3. No afirmar que una compilación no firmada está certificada por Microsoft, los fabricantes de FPGA o Digital.
4. Mantener las URL oficiales de componentes descargables, versiones fijadas y verificaciones SHA-256; revisar los nuevos hashes al actualizar.
5. Revisar el árbol y **todo el historial Git**, incluidos archivos eliminados y copias `.bundle`, antes de cambiar un repositorio privado a público.
6. Publicar los binarios solo después de aceptación real, conservar fuente/avisos y recordar que aprobar CI no demuestra ausencia de defectos ni compatibilidad con cualquier equipo.

## Independencia del proyecto

PhœnixForge no está afiliado oficialmente a Digital, Arduino, Icarus Verilog, Intel, AMD, Xilinx/AMD, Lattice, Gowin, Qt, Microsoft, OpenAI u otros terceros mencionados. Sus nombres se utilizan para identificación técnica y atribución, no como prueba de aprobación.
