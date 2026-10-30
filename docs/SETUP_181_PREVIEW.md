# PhœnixForge 1.8.1 Preview — instalador libre para FPGA

La rama feature/181-setup prepara un Setup x64 de Windows 10/11.
**No se fusionará con main ni se publicará como estable sin pasar CI Windows y
pruebas de hardware real.**

## Herramientas incluidas en un solo Setup

- PhœnixForge: editor, proyectos, Icarus, Hardware Studio, Arduino, Pico y
  herramientas de desarrollo que ya existían.
- OSS CAD Suite: sección seleccionada por defecto; descarga en instalación
  de la publicación oficial de YosysHQ (2026-10-27, Windows x64), unos 603 MB.
- Yosys: síntesis RTL de Verilog a netlist JSON/BLIF, sin Quartus.
- openFPGALoader: diagnóstico JTAG a solicitud del usuario, sin instalar drivers.
- Digital v0.31 y Java Temurin 21: opciones preexistentes, separadas.
- Las dependencias externas se alojan en Integrations dentro de la instalación
  por usuario. Se comprueba SHA256 de la descarga oficial. No se modifica PATH
  global, registro de drivers ni instalaciones del sistema.

**La descarga de 603 MB requiere Internet y espacio de almacenamiento adicional.
No es un Setup totalmente offline.** Si falla la descarga o verificación, la app
base puede instalarse, pero las herramientas libres no estarán preparadas.

SHA256 de OSS CAD Suite Windows x64:
aadcf3ff1b7cc8720509fde6c57ca84249f3beb45ddd14fd492c608241a12bb8

## Lo que todavía NO está terminado

El flujo totalmente independiente de Quartus para Cyclone IV aún necesita
mapeo tecnológico por part number, restricciones físicas, place-and-route,
generación de .rbf/.sof y validación física. Distribuir Yosys, nextpnr y
openFPGALoader NO equivale a un generador universal de bitstreams.
Cyclone_CRAM_Mapper es referencia GPL experimental para EP4CE6F17C8, pero
su bitgen no está conectado ni redistribuido en este Setup. No existe botón
de programación automática a partir de los netlists de Yosys.

Las pruebas de CI pueden certificar arranque de EXE y formato del Setup;
el cable JTAG, controladores, voltajes y pinout siguen sujetos a
pruebas con placas físicas. Mantener la 1.7.0 estable por separado.

Fuentes y licencias:
- https://github.com/YosysHQ/oss-cad-suite-build
- https://github.com/trabucayre/openFPGALoader
- https://github.com/YosysHQ/yosys
- https://github.com/14sea/Cyclone_CRAM_Mapper
