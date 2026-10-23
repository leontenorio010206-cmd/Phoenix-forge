# Tutorial: de PhœnixForge a Digital — contador FPGA de 4 bits

**Nivel:** introducción a Verilog y simulación RTL  
**Software:** PhœnixForge v1.7.0 + Icarus Verilog 12.0 + Digital v0.31 (opcional) + Java  
**Autoria del proyecto:** Leonardo Antonio Hernández Tenorio. Asistencia de IA: ChatGPT (OpenAI).

## Objetivo didáctico

Escribir/abrir un **contador binario de cuatro bits** en PhœnixForge, comprobarlo con un testbench en Icarus, exportar el módulo de diseño a **component.v**, agregarlo a **Digital** como **External File** y visualizar los cuatro bits con indicadores.

**NO es una demostración de síntesis, programación eléctrica ni emulación fiel de la FPGA física.** La selección de placa es un perfil informativo y la prueba sucede en software.

## 1. Preparación

1. Instala [PhœnixForge v1.7.0](https://github.com/leontenorio010206-cmd/Phoenix-forge/releases/tag/v1.7.0).
2. Durante el Setup marca Digital y Java, o ten disponibles una copia oficial de Digital.jar y un runtime Java compatible.
3. Abre el [proyecto .pforge del ejemplo](../examples/fpga_demo_profesor/Ejemplo_Contador_FPGA_4bits.pforge).
4. Antes de ejecutar código HDL ajeno, examínalo: una simulación no es una sandbox segura.

## 2. Comprende el módulo

Archivo **fpga_demo.v**:

\`\`\`verilog
module fpga_demo(input clk, input reset, output reg [3:0] leds);
  always @(posedge clk) begin
    if (reset) leds <= 4'b0000;
    else leds <= leds + 4'b0001;
  end
endmodule
\`\`\`

- **clk**: reloj; solo el **flanco ascendente** actualiza el contador.
- **reset**: reinicia las salidas a \`0000\` **en el siguiente flanco de reloj**, no en cualquier instante.
- **leds[3:0]**: cuatro bits del valor binario, \`0000\` a \`1111\`.
- El contador **suma 1 en cada flanco**, pasa de 15 a 0 por desbordamiento de cuatro bits.

El archivo **tb_fpga_demo.v** no se lleva a Digital como parte del componente. Es un **banco de pruebas** que genera reloj, aplica reset, observa 12 transiciones y usa \`$fatal\` si falla un valor.

## 3. Simulación primero en PhœnixForge

1. En la barra lateral entra a **Estudio HDL**.
2. Selecciona módulo **fpga_demo** y testbench **tb_fpga_demo**.
3. Pulsa **↻ Módulos** si no aparecen.
4. Pulsa **▶ Simular** o F5.
5. Comprueba la salida esperada:

\`\`\`text
PASS: 12 FPGA RTL vectors
\`\`\`

6. Abre **Señales VCD** y observa la evolución de \`clk\`, \`reset\` y \`leds[3:0]\`.
7. Guarda el proyecto si quieres conservar resultados. No confundas una traza interna anterior con una ejecución fallida posterior.

## 4. Exportación a Digital: ruta ZIP

1. Selecciona el panel **Exportar a Digital**.
2. En **Módulo principal**, elige **fpga_demo** (no \`tb_fpga_demo\`).
3. En **Puertos**, comprueba **clk (entrada)**, **reset (entrada)** y **leds[3:0] (salida, 4 bits)**.
4. Pulsa **⬇ Exportar componente ZIP**.
5. Guarda el ZIP y descomprímelo en una carpeta permanente, por ejemplo \`Documentos\ContadorFPGA-Digital\`.
6. Abre esa carpeta; debe contener:
   - \`component.v\`: Verilog del diseño, listo para enlazar.
   - \`ports.json\`: nombre del módulo, anchos, direcciones y SHA-256.
   - \`LEEME_DIGITAL.txt\`: guía breve de importación.
   - \`symbol.svg\` y \`connections.svg\`: vistas ilustrativas, no archivos funcionales de circuito Digital.

La exportación **integra el diseño**, pero no contiene por defecto un testbench en el componente ni crea un fichero \`.dig\`.

## 5. Alternativa rápida: Preparar y abrir Digital

1. En **Exportar a Digital**, elige **⚡ Preparar y abrir Digital**.
2. Acepta la preparación del runtime Icarus y la exportación sin ZIP.
3. PhœnixForge intenta usar el Digital.jar y Java instalados con el Setup; si no, selecciona **Digital.jar** oficial ya descomprimido.
4. El programa copia al portapapeles la **ruta a component.v**, la ubicación de **IVerilog** y los nombres/anchos de puertos.
5. Digital se abre como una **aplicación independiente**. La inserción del componente se realiza manualmente.

En esta ruta, el Verilog preparado se guarda normalmente bajo el perfil de usuario en \`%LOCALAPPDATA%\PhoenixForge\digital\components\PF_fpga_demo\component.v\`.

## 6. Configura Icarus/IVerilog en Digital

Si Digital indica «Icarus no instalado»:

1. En Digital abre **Editar → Ajustes** (en inglés **Edit → Settings**).
2. Localiza la sección **IVerilog**.
3. Selecciona la carpeta que PhœnixForge informa después de **Preparar y abrir Digital**, normalmente \`%LOCALAPPDATA%\PhoenixForge\digital\icarus\`. No apuntes al archivo ZIP descargado.
4. Aplica cambios y utiliza las opciones de comprobación disponibles en tu edición de Digital.

Los nombres de menú pueden variar por idioma de Digital. La función «Preparar y abrir» **no** escribe automáticamente las preferencias globales de Digital.

## 7. Inserta External File y conecta terminales

1. En el editor de Digital busca **External File** bajo la biblioteca de componentes (en algunas interfaces: **Componentes → Varios → VHDL/Verilog → Archivo externo**).
2. Selecciona fuente **Verilog**, vincula **component.v** (NO el ZIP) y ejecuta **Check/Comprobar** para reconocer sus puertos.
3. Comprueba que aparezcan **clk**, **reset** y **leds[3:0]**. Si Digital pide los campos manuales, en PhœnixForge usa **📋 Copiar ajustes de puertos**; el campo de aplicación es **IVerilog**.
4. Añade un generador de **reloj**, una **entrada lógica** o interruptor para reset, y un **splitter** de bus para separar los cuatro bits de leds.
5. Conecta las cuatro salidas del splitter a **cuatro indicadores LED**. El orden de bits es \`leds[3]\` (MSB) hasta \`leds[0]\` (LSB).
6. Activa la simulación de Digital. Mantén **reset=1** durante un flanco ascendente para fijar \`0000\`; después pon **reset=0** y deja avanzar el reloj.
7. Observa los estados **0000 → 0001 → 0010 → 0011 ...**. Guarda el circuito como \`.dig\` **en una carpeta donde no se pierda la referencia al component.v**.

### Diagrama conceptual de conexiones

\`\`\`text
[Reloj Digital] ───────► clk
[Interruptor reset] ───► reset        ┌───────────────────┐
                                     │ FPGA_DEMO · RTL   │
                                     │                   │
                                     │      leds[3:0] ───┼──► [Splitter] ─► LED3, LED2, LED1, LED0
                                     └───────────────────┘
\`\`\`

*Diagrama lógico ilustrativo, no un esquema eléctrico ni captura de Digital.*

## 8. Comprobaciones que puede presentar el alumno

| Etapa | Evidencia |
|---|---|
| Fuente | \`fpga_demo.v\` visible en el editor |
| Validación | Consola con «PASS: 12 FPGA RTL vectors» |
| Ondas | VCD con reloj, reset y contador |
| Exportación | Carpeta con \`component.v\` y \`ports.json\` |
| Digital | External File conectado, LEDs cambiando al pulso |
| Guardado | Archivo \`.dig\` creado en Digital por el usuario |

El video explicativo ubicado en el paquete del profesor **es una recreación didáctica de pantallas, no una grabación de ejecución real**. Las evidencias experimentales deben capturarse con el programa abierto en el equipo.

## 9. Solución de problemas de Digital

- **Digital.jar no abre**: instala Java o usa el JRE descargado por Setup; comprueba que seleccionas Digital.jar y no Digital.zip.
- **No se encontró IVerilog**: configura su ruta una vez en **Editar → Ajustes → IVerilog**.
- **No aparecen puertos**: selecciona \`component.v\`, no \`tb_fpga_demo.v\`; verifica el tipo Verilog y pulsa Check.
- **Los LED no cambian**: el reset es **síncrono**, necesita un flanco; para contar baja reset a 0 y genera flancos ascendentes.
- **El circuito .dig pierde el enlace**: conserva \`component.v\` en la carpeta permanente y revisa la referencia.
- **Se esperaba un bitstream**: el botón de exportación produce **RTL Verilog**, no un archivo de programación física.

## 10. Derechos y atribuciones

Digital: © respectivos autores, proyecto de Helmut Neemann, **GNU GPLv3**, https://github.com/hneemann/Digital. PhœnixForge: código propio MIT, fuente original y avisos de terceros en el repositorio. Son proyectos independientes, sin patrocinio ni aval entre sí.

**Manual de práctica elaborado para acompañar PhœnixForge v1.7.0.**
