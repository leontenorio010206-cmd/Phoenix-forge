# Hacia Cyclone IV sin Quartus: experimento previo a v1.8.1

Rama: feature/cyclone-iv-open-toolchain (mantener main sin cambios).

## Lo que hace YA

Hardware Studio → Cyclone IV / Libre ofrece síntesis lógica de proyectos
.pforge mediante Yosys. Produce netlist.json, netlist.blif y yosys.log.
No invoca Quartus, JTAG ni controladores USB.
Puede localizar Yosys en PATH o en tools/ y bin/ del paquete congelado.

IMPORTANTE: que PhoenixForge encuentre un Yosys empaquetado NO significa
que el instalador público 1.7 incluya ese ejecutable. También habrá que
empaquetar sus dependencias con hashes, licencias y pruebas nativas Windows.

## Lo que falta para programar la Cyclone IV

La síntesis genérica no conoce el bitstream de cada FPGA. La cadena completa
requiere el mapa de celdas LUT y RAM, modelos de timing, enrutamiento, I/O,
relojes, un generador RBF/SOF y pruebas sobre placa real.
En esta rama **NO SE GENERA ningún bitstream físico** y por lo tanto el
programador no acepta los netlists como firmware.

Proyecto abierto prometedor: https://github.com/14sea/Cyclone_CRAM_Mapper
El autor reporta Yosys → nextpnr-generic → np2fasm → fasm2rbf para
EP4CE6F17C8 y algunas pruebas físicas, con limitaciones de ruteo a escala
y de cobertura de modelos. Ningún otro EP4CE/EP4CGX se considera soportado
por ese bitgen. El diagnóstico ep4ce6_research_status inspecciona archivos
locales del proyecto sin importar ni ejecutar su código.

Licencias: Cyclone_CRAM_Mapper usa GPL-3.0-or-later en código y CC BY-SA 4.0
en documentación. PhoenixForge MIT mantiene interfaz por procesos separada;
no se han copiado ni integrado fuentes GPL. Una futura distribución deberá
incluir las licencias y cumplir las obligaciones correspondientes.

Próximos pasos:
1. Empaquetar Yosys sin instalación manual con verificación criptográfica.
2. Integrar un backend físico EP4CE6 experimental como proceso externo GPL.
3. Crear/validar chipdb, restricciones, ruteo y codificación CRAM/RBF.
4. Probar pruebas diferenciales, CRC y diseños con placa real.
5. Añadir botón de programación SRAM solo tras pruebas y confirmación física.

No confundir pruebas unitarias simuladas ni CI Windows con prueba de silicio.
