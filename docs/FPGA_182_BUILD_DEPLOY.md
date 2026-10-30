# PhœnixForge 1.8.2 Preview — FPGA Cyclone IV

Esta rama incorpora síntesis lógica sin Quartus mediante Yosys, importación de RBF externo, verificación SHA256, lectura JTAG previa y carga temporal a SRAM. **No genera todavía un bitstream físico Cyclone IV desde RTL y no ha sido probada en una placa real.**

## Setup

El Setup Windows 10/11 x64 1.8.2 mantiene OSS CAD Suite Yosys/openFPGALoader como descarga oficial verificada durante instalación (~603 MB), con Java y Digital opcionales. No modifica PATH ni controladores globales. No es instalador completamente sin conexión.

## Uso del asistente Cyclone IV / Libre

1. Sintetiza Verilog a JSON/BLIF con Yosys. Estos archivos NO sirven para programar directamente la FPGA.
2. Para cargar un diseño, selecciona un RBF obtenido de un compilador específico para el marcado y encapsulado de tu placa. Revisa esquema, pines, voltajes y nombre/revisión. PhœnixForge almacena una copia y su checksum con advertencia 'EXTERNAL_RBF_UNVERIFIED'.
3. Confirma manualmente la placa y la carga solo a SRAM. La app vuelve a leer el IDCODE, comprueba integridad y solicita confirmación. Solo se usa openFPGALoader `-m`, nunca se escribe Flash (`-f`).

El IDCODE no identifica por sí solo la placa, encapsulado o pinout. Una programación con respuesta exitosa del cargador NO significa que el comportamiento en silicio haya sido comprobado.

## Compilación física libre pendiente

Generar RBF a partir de RTL sin Quartus requiere para cada chip mapeo tecnológico, datos de celdas, place-and-route, restricciones físicas, bitgen y ensayos reales. La investigación experimental para EP4CE6F17C8 está en https://github.com/14sea/Cyclone_CRAM_Mapper (GPL-3.0-or-later). El proyecto todavía usa datos específicos y bitstreams base de referencia; no certificamos ni redistribuimos un backend físico completo.

Para el flujo clásico con Quartus instalado por separado sigue existiendo el asistente Cyclone IV / Quartus; la ruta libre no instala ni requiere Quartus para síntesis.

Validación requerida antes de declarar estable: CI nativa Windows y Setup, pruebas de instalador real y prueba de hardware con placa física verificada.
