# Manual de usuario — PhœnixForge v1.7.0

**Primera versión estable de Windows x64 (validada por CI)**  
**Cofundador, cocreador y mantenedor:** Leonardo Antonio Hernández Tenorio  
**Asistencia técnica y documentación:** ChatGPT (OpenAI), herramienta de IA  
**Proyecto:** https://github.com/leontenorio010206-cmd/Phoenix-forge  
**Publicación estable:** https://github.com/leontenorio010206-cmd/Phoenix-forge/releases/tag/v1.7.0

> **Alcance real:** PhœnixForge permite diseñar y verificar módulos Verilog en una simulación lógica RTL y exportar su código para utilizarlo en el simulador **Digital** de Helmut Neemann. **No** emula el silicio físico de una FPGA, sus retardos, PLL, voltajes, periféricos o pines eléctricos; **no** genera bitstreams por el solo hecho de elegir un perfil.

## 1. ¿Qué es PhœnixForge?

Es un IDE educativo para proyectos de electrónica digital en archivos **.pforge**. Integra editor HDL, simulación real con Icarus Verilog, visualizador de señales VCD, banco virtual de entradas/salidas, perfiles informativos de FPGA, exportación para Digital y un panel de hardware con dependencias específicas.

En Windows 10/11 de 64 bits, la versión **1.7.0** tiene una compilación de Setup y Portable aceptada por GitHub Actions. «Estable» aquí significa que superó pruebas automáticas; no sustituye ensayos en todas las laptops o placas.

## 2. Instalación y primer arranque

1. Abre la [Release v1.7.0](https://github.com/leontenorio010206-cmd/Phoenix-forge/releases/tag/v1.7.0).
2. Descarga **PhoenixForge_v1.7.0_Setup.exe** o **PhoenixForge_v1.7.0_Portable.exe** y **SHA256SUMS.txt**.
3. Comprueba la suma SHA-256 con PowerShell si necesitas validar la integridad del archivo.
4. **Setup:** instala PhœnixForge para tu usuario. Marca *Digital v0.31* y *Java Temurin 21* únicamente si usarás Digital y tienes conexión.
5. **Portable:** ejecuta el EXE directamente, sin asistente. Digital y Java no están incluidos en este archivo; son opcionales.
6. En la pantalla **Configuración** deja vacías las rutas manuales de **iverilog** y **vvp** para usar Icarus incluido en el Windows completo.

Consulta [Manual de instalación](INSTALLATION_MANUAL.md) para requisitos, verificación, actualización, desinstalación y problemas comunes.

## 3. Conoce las ocho secciones principales

| Sección | Uso |
| --- | --- |
| Inicio | Crear/abrir proyectos y acceder a funciones |
| Estudio HDL | Editar código Verilog, seleccionar módulo y testbench, simular |
| Dispositivos FPGA | Elegir uno de diez perfiles, crear una demo RTL y asignar pines como metadatos |
| Proyectos de muestra | Abrir ejemplos de semáforo, divisores, sumadores y contadores |
| Exportar a Digital | Ver puertos y símbolo, crear ZIP del componente o preparar/abrir Digital |
| Hardware Studio | Inspección y herramientas para Arduino, Raspberry Pi Pico, USB/JTAG y FPGA según plataforma |
| Plugins | Descubrir y cargar extensiones de confianza |
| Configuración | Definir rutas externas y preferencias |

**Nota:** seleccionar un perfil de FPGA no implica conectar ni programar físicamente ese chip. El sistema USB/JTAG requiere drivers y placas compatibles; no se debe flashear firmware que no corresponda exactamente al hardware.

## 4. Proyectos .pforge

- En **Archivo → Nuevo proyecto**, crea tu proyecto de Verilog.
- En **Archivo → Abrir proyecto**, selecciona un archivo **.pforge**.
- Guarda desde **Archivo → Guardar** (Ctrl+S) o Guardar como (Ctrl+Shift+S).
- Un .pforge contiene fuentes, configuración, metadatos y resultados conservados; verifica estructura y SHA-256 al abrir.
- Desde **Estudio HDL → + Archivo**, crea fuentes, o utiliza **Importar** para agregar archivos externos.
- Abrir un archivo fuente en otra pestaña no lo elimina del proyecto al cerrar esa pestaña.
- No ejecutes HDL de terceros sin revisarlo: la simulación se ejecuta con los permisos de tu usuario.

### Atajos útiles

| Atajo | Acción |
| --- | --- |
| Ctrl+N / Ctrl+O | Proyecto nuevo / abrir |
| Ctrl+S / Ctrl+Shift+S | Guardar / guardar como |
| Ctrl+I | Importar |
| Ctrl+F | Buscar texto |
| F5 / Shift+F5 | Simular / detener |
| Ctrl+Z / Ctrl+Y | Deshacer / rehacer |

## 5. Simular un circuito Verilog (paso a paso)

Usaremos el [ejemplo docente](../examples/fpga_demo_profesor/README.md) del **contador de 4 bits**.

1. Abre \`examples/fpga_demo_profesor/Ejemplo_Contador_FPGA_4bits.pforge\`.
2. Navega a **Estudio HDL**.
3. En **Módulo**, elige **fpga_demo**. En **Testbench / raíz**, elige **tb_fpga_demo**.
4. Pulsa **↻ Módulos** si editaste o importaste código y faltan opciones.
5. Pulsa **▶ Simular** (F5).
6. En **Consola**, identifica la línea esperada **PASS: 12 FPGA RTL vectors**.
7. En **Señales VCD**, examina el archivo **fpga_demo.vcd**: reloj, reset y bus \`leds[3:0]\`.
8. Guarda el proyecto para preservar sus resultados.

El testbench provoca doce flancos ascendentes, verifica un reset síncrono activo alto y comprueba los valores 1 a 12 del contador. **La frase PASS es el resultado esperado del testbench**, no una lectura eléctrica de una placa real.

### ¿Por qué son importantes los testbenches?

El editor compila código Verilog mediante **Icarus Verilog** (\`iverilog\` y \`vvp\`). El testbench genera estímulos y usa \`$fatal\` cuando hay diferencias; \`$dumpfile\` y \`$dumpvars\` crean una traza VCD. Compilar sin errores no demuestra que el diseño sea correcto: el banco de pruebas debe comprobar la lógica.

### Errores típicos

- **No se encontraron iverilog y vvp:** deja vacías las rutas personalizadas si usas Windows Setup/Portable completo.
- **Módulo principal no existe:** revisa su nombre y pulsa **↻ Módulos**.
- **Simulación termina sin señales:** asegúrate de tener un testbench con \`$dumpfile\`, \`$dumpvars\` y \`$finish\`.
- **Se excede el tiempo:** revisa un bucle sin fin y el límite configurado (1–120 segundos).
- **La consola muestra un error de Verilog:** revisa **Errores y advertencias** y la línea indicada.

## 6. Laboratorio FPGA virtual

En **Dispositivos FPGA → FPGA virtual · E/S**, PhœnixForge puede generar estímulos para entradas RTL, flancos de reloj y observar salidas del módulo. Puedes seleccionar uno de los perfiles y crear una demostración con **Crear demo RTL para esta FPGA**.

La simulación es **funcional genérica**: no reproduce temporización, relojes internos de fabricante, sintetización, memoria física del dispositivo ni tensión real de pines. Las asignaciones de pines en el proyecto son **solo metadatos**.

## 7. Exportar tu diseño hacia Digital

Hay dos caminos:

### Opción A: ZIP de componente

1. Ve a **Exportar a Digital**.
2. En **Módulo principal**, selecciona \`fpga_demo\` (nunca \`tb_fpga_demo\`).
3. Comprueba las entradas **clk**, **reset** y salida **leds[3:0]**.
4. Pulsa **⬇ Exportar componente ZIP** y guarda el archivo.
5. **Descomprime** el ZIP en una carpeta permanente. Dentro verás \`component.v\`, \`ports.json\`, \`LEEME_DIGITAL.txt\`, \`symbol.svg\` y \`connections.svg\`.
6. En Digital añade un componente **External File** de tipo **Verilog**, selecciona el archivo **component.v** y conecta su reloj, reset y bus \`leds\`.
7. Configura **Icarus/IVerilog** en Digital si te lo pide. Guarda tu circuito \`.dig\` cerca de la carpeta del componente para mantener la ruta al HDL.

### Opción B: asistencia integrada

1. En la misma pantalla selecciona **⚡ Preparar y abrir Digital**.
2. Confirma la operación. PhœnixForge prepara \`component.v\` sin comprimir y copia un runtime Icarus verificado en el área de datos del usuario.
3. Si instalaste Digital y Java mediante el Setup, el puente puede encontrarlos automáticamente; si no, selecciona **Digital.jar**.
4. Digital se abre aparte. Si solicita IVerilog, entra en **Editar → Ajustes → IVerilog** y usa la ruta que PhœnixForge copia al portapapeles.
5. **Aún debes colocar External File, seleccionar component.v, conectar terminales y simular dentro de Digital.**

El ZIP **no** se selecciona como componente. Los SVG son **ilustraciones de referencia**, no símbolos instalados automáticamente. **PhœnixForge no fabrica un circuito .dig terminado ni un plugin Java .jar con este flujo.**

Véase [Tutorial completo: FPGA RTL a Digital](DIGITAL_TUTORIAL.md).

## 8. Interpretar los cuatro terminales del ejemplo

\`fpga_demo\` tiene **clk** (entrada de reloj), **reset** (entrada que reinicia al próximo flanco ascendente) y \`leds[3:0]\` (salida de cuatro bits). Conecta el bus a un divisor de bus y cuatro indicadores, o a una visualización digital de 4 bits compatible con Digital.

| Condición en un flanco ascendente | Resultado esperado |
| --- | --- |
| reset = 1 | leds = 0000 |
| reset = 0, primer pulso | leds = 0001 |
| reset = 0, segundo pulso | leds = 0010 |
| reset = 0, duodécimo pulso | leds = 1100 |

En Digital pulsa las entradas y deja que el reloj genere los flancos. Si no observas cambios, comprueba el reset, la configuración de IVerilog y el correcto enlace de \`component.v\`.

## 9. Evidencias recomendadas para evaluación académica

1. Captura del editor mostrando \`fpga_demo.v\`.
2. Captura de la consola con el texto esperado **PASS: 12 FPGA RTL vectors**.
3. Captura del visor VCD con cambios del bus.
4. Captura de **Exportar a Digital** mostrando puertos.
5. Carpeta con el \`component.v\` exportado.
6. Captura de Digital con el componente conectado y la simulación corriendo.
7. Explicación explícita de qué se ha simulado en software y qué **no** se ha programado en una FPGA real.

Estas capturas deben obtenerse ejecutando las aplicaciones. No confundir ilustraciones del tutorial con evidencia experimental.

## 10. Seguridad, licencias y soporte

- Código original PhœnixForge: [MIT](../LICENSE), © 2026 Leonardo Antonio Hernández Tenorio.
- Digital de Helmut Neemann: software independiente bajo GPLv3, descargable opcionalmente. [Repositorio oficial](https://github.com/hneemann/Digital).
- Icarus, Qt/PySide6, Python y Java conservan sus licencias. Consulta [LEGAL.md](../LEGAL.md) y [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
- Archivos propios: \`%LOCALAPPDATA%\PhoenixForge\` en Windows. La desinstalación no debe interpretarse como eliminación de los proyectos del usuario.
- Windows 7, 32 bits y programación universal de FPGA no están certificados en esta Release.
- Errores reproducibles: [GitHub Issues](https://github.com/leontenorio010206-cmd/Phoenix-forge/issues).

**Material educativo basado en el código público PhœnixForge v1.7.0.** La integración con Digital es independiente y no implica aval de su autor.
