# PhœnixForge v1.7.0 — Primera versión estable para Windows x64

**Estado:** primera distribución que ha superado la puerta de aceptación nativa automatizada en Windows de GitHub Actions. Estabilidad verificada en CI, no certificación de compatibilidad universal ni promesa de ausencia de errores.

**Proyecto y mantenimiento:** Leonardo Antonio Hernández Tenorio, **cofundador, cocreador y mantenedor principal**. Asistencia técnica de IA: **ChatGPT (OpenAI)**, acreditada como herramienta colaboradora, no como cofundador jurídico ni propietario. GitHub: [@leontenorio010206-cmd](https://github.com/leontenorio010206-cmd).

## ¿Qué incluye?

- Editor Verilog/SystemVerilog, proyectos `.pforge`, plantillas educativas y autopruebas.
- Simulación funcional RTL con **Icarus Verilog 12.0**, visor VCD, banco virtual de entradas/salidas y ejemplos de FPGA.
- Exportación Verilog para Digital, puente asistido para abrir `Digital.jar`, y un Setup modular.
- Integraciones de hardware para Arduino/Pico/FPGA y diagnóstico de USB/JTAG: según modelo, requieren herramientas externas, firmware adecuado y pruebas con la placa física.
- Menor trabajo de CPU cuando Hardware Studio está oculto, adaptación de ventana para pantallas pequeñas y generación de informes de tamaño. **No se afirma una reducción de megabytes sin una comparación medida.**
- Validación de Windows con pruebas completas de código, autopruebas empaquetadas, arranque GUI y SHA-256. No se emiten binarios aprobados si falla la aceptación.

## Instalación

**Windows 10/11 x64** (Windows 10 versión 1809 o posterior para Setup). Windows 7 y x86 de 32 bits no están certificados.

1. Descarga los ejecutables directamente desde los **Assets** de esta GitHub Release.
2. Comprueba `SHA256SUMS.txt` para verificar los archivos descargados.
3. Inicia `PhoenixForge_v1.7.0_Setup.exe` para la instalación por usuario, o utiliza `PhoenixForge_v1.7.0_Portable.exe`.
4. Marca **Digital v0.31** y **Java Eclipse Temurin 21** únicamente si vas a usar Digital y tienes conexión a Internet; el Setup verifica los paquetes oficiales.

El instalador no requiere privilegios de administrador y no modifica el PATH del sistema ni controladores USB/JTAG. No firma los ejecutables; algunos antivirus/SmartScreen pueden solicitar comprobaciones adicionales. Conserva tus proyectos antes de cambiar de versión.

## Pruebas e incompatibilidades conocidas

- Aprobada en Windows Server 2022 de GitHub Actions, con herramientas de desarrollo retiradas del PATH al validar el ejecutable congelado.
- No sustituye ensayos de campo en Windows Home/Pro, equipos de 4 GB RAM, discos HDD, antivirus distintos o pantallas pequeñas.
- La “FPGA virtual” **no** reproduce tiempos, PLL, silicio, recursos ni voltajes de placas reales. Los bitstreams deben coincidir con hardware concreto y no hay garantía de compatibilidad universal.
- Las herramientas y plugins de terceros pueden requerir configuración adicional. Nunca instales drivers JTAG automáticamente sin confirmar el hardware.
- La integración con Digital abre un simulador independiente; la generación automática completa de archivos `.dig` no está certificada.

## Autoría, agradecimientos y licencias

**PhœnixForge:** código propio con licencia [MIT](https://github.com/leontenorio010206-cmd/Phoenix-forge/blob/main/LICENSE), © 2026 Leonardo Antonio Hernández Tenorio.

**Gracias a Helmut Neemann por [Digital](https://github.com/hneemann/Digital)**, simulador educativo libre bajo **GNU GPLv3**. Digital no forma parte del código de PhœnixForge ni respalda oficialmente esta aplicación. La instalación opcional descarga el ZIP de Digital sin reempaquetarlo como código nuestro.

También reconocemos a Icarus Verilog, Qt/PySide6, Python, Eclipse Temurin, PyInstaller, NSIS y comunidades FPGA/Arduino. Todas las dependencias conservan sus licencias; consulta [avisos de terceros](https://github.com/leontenorio010206-cmd/Phoenix-forge/blob/main/THIRD_PARTY_NOTICES.md), [créditos](https://github.com/leontenorio010206-cmd/Phoenix-forge/blob/main/CREDITS.md) y [nota legal](https://github.com/leontenorio010206-cmd/Phoenix-forge/blob/main/LEGAL.md).

## Publicación y verificaciones

- Esta versión se publica únicamente cuando el proceso de Windows ha aprobado las pruebas automatizadas y se han contrastado los archivos de Release con sus SHA-256.
- Si se abre el repositorio al público, primero se debe revisar **el historial Git completo**, los archivos `.bundle`, credenciales y datos privados: eliminar un archivo del último commit **no** lo borra de commits anteriores.
- Debe hacerse disponible el código fuente y documentación de licencias pertinente a los binarios redistribuidos.

Muchas gracias por acompañar el desarrollo de esta primera edición estable. Se agradecen informes de errores reproducibles y contribuciones con pruebas.
