# Ejemplo para el profesor — contador RTL de FPGA (4 bits)

**Compatible con PhœnixForge v1.7.0.** Este directorio contiene un proyecto editable en formato \`.pforge\` y fuentes Verilog visibles para revisar en clase.

## Archivos

- [Ejemplo_Contador_FPGA_4bits.pforge](Ejemplo_Contador_FPGA_4bits.pforge): proyecto completo con inventario SHA-256, módulo y testbench.
- [fpga_demo.v](fpga_demo.v): contador binario ascendente de cuatro bits.
- [tb_fpga_demo.v](tb_fpga_demo.v): testbench con reset síncrono, 12 comprobaciones y traza VCD.
- [Manual de usuario](../../docs/USER_MANUAL.md).
- [Tutorial de Digital](../../docs/DIGITAL_TUTORIAL.md).

## Abrir y verificar

1. En PhœnixForge: **Archivo → Abrir proyecto** y selecciona el archivo \`.pforge\` de esta carpeta.
2. En **Estudio HDL** selecciona **Módulo: fpga_demo**, **Testbench / raíz: tb_fpga_demo**.
3. Pulsa **▶ Simular** (F5). El testbench está diseñado para mostrar \`PASS: 12 FPGA RTL vectors\`.
4. Abre **Señales VCD** para observar \`clk\`, \`reset\` y \`leds[3:0]\`.
5. En **Exportar a Digital** elige **fpga_demo** y pulsa **⬇ Exportar componente ZIP**. **Descomprime** ese ZIP; el archivo que Digital debe usar es **component.v**, no el ZIP ni el testbench.
6. En Digital inserta **External File** de tipo **Verilog** y selecciona \`component.v\`. Configura IVerilog en los ajustes si falta; conecta reloj, reset y un divisor de bus para cuatro LEDs.

## Función física

\`\`\`text
              ┌───────────────┐
CLK ──────────►│               │       LEDs [3:0]
RESET ────────►│   FPGA_DEMO   ├─────────────────►  4 bits
              │   Verilog     │
              └───────────────┘
\`\`\`

El reset es **síncrono**: en un flanco positivo con reset=1, \`leds=0000\`. Luego con reset=0, en los siguientes flancos positivos verás \`0001\`, \`0010\`, \`0011\`, ... hasta \`1100\` en el duodécimo vector.

**No genera bitstream ni valida la placa real.** El perfil EP2C5 del archivo es informativo; cualquier prueba física requiere herramienta, cable y archivo de programación adecuados a la placa.

## Atribución

Fuentes del ejemplo basadas en la demostración \`device_demo_project\` de \`app/devices/simulation.py\` de PhœnixForge v1.7.0. Código propio MIT; el uso opcional de Digital (Helmut Neemann) es independiente, GPLv3.
