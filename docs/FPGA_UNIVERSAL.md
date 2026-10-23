# FPGA universal — detección asistida y compatibilidad real

La meta es que PhoenixForge ofrezca **un único entorno de edición y control**
para FPGA de distintos fabricantes, pero **un chip no se puede programar
por el mero hecho de que el cable se conectó por USB**.

La pestaña **Hardware Studio → FPGA universal** (rama de desarrollo) agrega
un diagnóstico conservador:

1. **Revisar compiladores FPGA:** muestra qué binarios encuentra en el PATH
   (Quartus, Yosys, nextpnr, etc.). Encontrar un programa **no equivale** a
   confirmar que puede crear un bitstream para el chip conectado.
2. **Seleccionar openFPGALoader:** usa la instalación que el usuario haya
   elegido o esté disponible en el PATH; no descarga ejecutables/drivers.
3. **Seleccionar un cable:** el usuario puede escribir o elegir
   `usb-blaster`, `ft2232`, `cmsisdap`, etc. «Sugerir por USB» solo identifica
   tentativamente el **adaptador**, nunca el chip o la placa. No se realizan
   exploraciones JTAG al detectar automáticamente un dispositivo USB.
4. **Leer chip por JTAG:** al pulsar el botón ejecuta exclusivamente
   `openFPGALoader --detect -c CABLE`. Esto no programa la memoria ni Flash.
   Muestra el resultado original y, cuando puede, un nombre de familia
   **tentativo**. Si no reconoce el dispositivo, mantiene estado desconocido.
5. **Configurar proyecto físico:** es un paso **distinto**. Aunque JTAG
   identifique la densidad de un FPGA, puede no identificar el encapsulado,
   modelo de placa, reloj, pinout o estándar I/O. Usa la serigrafía del chip,
   manual de placa y conexiones verificadas para completar esos datos.

## Tabla honesta de herramientas

| Familia | Generación de bitstream | Integración física en PhoenixForge |
| --- | --- | --- |
| Cyclone IV | Quartus Prime con soporte Cyclone IV | Integración inicial bajo prueba (SRAM/JTAG) |
| Cyclone V | Quartus compatible | Pendiente |
| Lattice iCE40 | Yosys + nextpnr-ice40 + IceStorm para los modelos soportados | Pendiente |
| Lattice ECP5 | Yosys + nextpnr-ecp5 + Project Trellis | Pendiente |
| Gowin GW1/GW2/GW5 | EDA Gowin o soluciones abiertas según modelo | Pendiente |
| AMD/Xilinx serie 7 | Vivado u otros flujos específicos | Pendiente |
| Spartan-6 | ISE (legacy) | Pendiente |
| Efinix | Efinity | Pendiente |

**Universal significa arquitectura con adaptadores para cada fabricante**,
no un compilador mágico único. Las herramientas abiertas `nextpnr` no
generan bitstreams Cyclone IV; el soporte Cyclone V continúa experimental.
No hay promesa de soporte total para todas las variantes.

## Reglas de seguridad

- Sin programación automática al conectar un cable.
- Nunca se genera un pinout a partir de VID/PID USB ni de JTAG.
- Una familia probable detectada no equivale a un chip validado.
- Las interfaces sin drivers o conexiones correctas reportan el error.
- Sin firmware genérico universal para FPGA.
- Flash y firmware de arranque se mantienen fuera del asistente universal.
- No se instala software de terceros sin intervención del usuario.
- El flujo integrado de Cyclone IV exige chip exacto, todos los pines y
  confirmación explícita; no se activa desde la pestaña universal.

## Qué funciona ya y qué falta

**Implementado en esta rama:** diagnóstico por JTAG bajo demanda,
detección conservadora de familia, listado de toolchains encontrados,
sugerencia de cable USB y pruebas automatizadas sin hardware.

**Pendiente:** pilotos de síntesis propios para cada familia, perfiles
verificados de tarjetas, pinout asociado al modelo exacto, validación
con cables y placas reales, y nuevas pruebas de empaquetado Windows.

Fuentes técnicas:

- https://trabucayre.github.io/openFPGALoader/guide/first-steps.html
- https://github.com/trabucayre/openFPGALoader
- https://github.com/YosysHQ/nextpnr
