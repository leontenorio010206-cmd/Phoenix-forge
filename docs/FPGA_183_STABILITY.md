# PhœnixForge 1.8.3 Preview — estabilidad FPGA

Rama experimental: feature/183-stability. Main/v1.7.0 sigue intacto.

## Correcciones reales

* Detección JTAG rechaza varios IDCODE aunque sean idénticos, modelos físicos ambiguos y cable o cadena inexistente.
* RBF externo revisado tras JTAG, copiado a archivo temporal, verificado otra vez y eliminado al concluir. Solo comando SRAM temporal; nunca Flash.
* Se comprueban nombres y duplicados de pines en manifiestos. Se rechazan entradas simbólicas como fuente RBF.
* Recibos de OSS CAD Suite comprueban SHA256 de los binarios, incluido nextpnr-generic cuando existe. Instala en carpeta privada sin PATH global.
* La UI localiza Yosys, no preselecciona cable, y revoca confirmaciones al importar otro firmware o al efectuar un intento. Los paquetes de otro proyecto activo se rechazan.
* Setup Windows 1.8.3 con versionado y reporte de aceptación propios; OSS CAD Suite 2026-10-27 descargada con hash oficial (~603 MB). Java y Digital siguen opcionales.

## Alcance exacto

Yosys sintetiza Verilog a JSON/BLIF SIN Quartus. Puede importar un RBF preexistente y verificarlo, leer JTAG y cargar a SRAM solo con consentimiento. No garantiza la validez de un RBF externo ni el comportamiento físico. Requiere que el usuario verifique serigrafía, esquema, voltajes, encapsulado, cable y pines.

**Aún no genera de forma libre bitstreams físicos Verilog → RBF para todos los Cyclone IV.** La investigación GPL https://github.com/14sea/Cyclone_CRAM_Mapper está limitada a EP4CE6F17C8 y todavía presenta restricciones experimentales de ruteo y mapeo.

## Pruebas pendientes

El CI de fuentes y Windows permite detectar regresiones en software, pero hace falta validar instalación en PC real y funcionamiento en FPGA física. No publicar como estable ni prometer compatibilidad universal sin esas verificaciones.
