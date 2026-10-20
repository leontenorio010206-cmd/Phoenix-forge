# PhœnixForge v1.6.2 — FPGA Studio y diagnóstico de controladores

## Qué se detecta realmente

Un chip FPGA normalmente no aparece como dispositivo USB. Windows ve **la interfaz del programador**
(JTAG, USB-Blaster, FTDI, CMSIS-DAP, etc.) y puede usar drivers distintos según la
interfaz concreta (por ejemplo un cable con JTAG y puerto serie simultáneos).

**Hardware Studio → FPGA / Drivers** permite seleccionar una interfaz USB detectada
y consultar en Windows:

- ID de instancia e interfaz (`MI_00`, `MI_01`...).
- Nombre, estado, servicio, código de error PnP.
- Proveedor, versión, nombre del archivo INF del controlador firmado.
- Advertencias de compatibilidad, con especial atención a drivers FTDI y WinUSB/libusb.

**No se instala, cambia ni elimina ningún controlador automáticamente.** Un driver WinUSB
en la interfaz USB equivocada puede inutilizar temporalmente UART u otras funciones de
la placa. Para recuperar funcionalidad sigue las instrucciones del fabricante o la documentación
del controlador actual; no hagas sustituciones genéricas por VID/PID.

El VID `09FB` puede corresponder a un USB-Blaster original o clon; un FTDI (`0403`)
puede ser un cable JTAG o cualquier periférico USB. La etiqueta "rusa" o "china"
no basta para identificar chip, fabricante ni tipo de programador.

## Catálogo de FPGA: dinámico

PhœnixForge ofrece atajos de ejemplo a distintas familias:
Sipeed Tang Nano/Nano 4K/Nano 9K/Nano 20K (Gowin),
QMTech Cyclone IV/V (Intel/Altera), ULX3S/OrangeCrab (Lattice ECP5),
iCEBreaker (Lattice iCE40), Digilent Arty A7 (AMD/Xilinx Artix),
Terasic DE10-Nano, Efinix FireAnt.

El soporte efectivo **no lo fija la lista de atajos**: se consulta desde la
versión de `openFPGALoader` que el usuario instale y elija:
`--list-boards`, `--list-cables`, `--list-fpga`.

Para una FPGA sin nombre comercial conocido puedes utilizar una configuración
`-c` del programador si la herramienta admite ese cable. Para el chip concreto,
JTAG puede exponer un IDCODE cuando la conexión está bien configurada.
La detección no demuestra compatibilidad para sintetizar HDL ni instalar drivers.

## Uso

1. Instala openFPGALoader siguiendo documentación oficial (por ejemplo, MSYS2)
   o proporciona tu `openFPGALoader.exe` de confianza, junto con sus dependencias.
2. En `FPGA / Drivers`, pulsa **Seleccionar EXE**, después consulta el catálogo.
3. Selecciona la interfaz USB en el panel de la izquierda y pulsa
   **Diagnosticar driver Windows** para ver el controlador real.
4. Selecciona una placa compatible (`-b`) o un cable (`-c`) y pulsa
   **Detectar chip por JTAG**. No escribe bitstream ni instala drivers.
5. Para programación física, utiliza un bitstream generado específicamente
   para **ese chip y su placa**, y elige SRAM (temporal) o FLASH (persistente).
   Toda operación pide permiso y FLASH pide una segunda confirmación.

### Límites

- No incluye sintetizadores universales ni crea bitstreams de cualquier FPGA.
- No garantiza poder programar todas las FPGA comerciales o históricas.
- Windows 7 no se certifica en el empaquetado Qt/Python actual.
- Ni la procedencia china/rusa ni el precio tienen relación directa con su ID USB.
- Se necesita hardware real para validar cada cable y placa. Las pruebas de
  desarrollo simulan salidas de comandos y diagnóstico de Windows.
- La función programadora necesita `openFPGALoader` de confianza que suministre
  el usuario; no se descargan ejecutables externos sin verificación de integridad.

### Referencias

- https://github.com/trabucayre/openFPGALoader
- https://trabucayre.github.io/openFPGALoader/guide/install.html
- https://trabucayre.github.io/openFPGALoader/compatibility/board.html
- https://trabucayre.github.io/openFPGALoader/compatibility/cable.html
- https://www.sipeed.com/
