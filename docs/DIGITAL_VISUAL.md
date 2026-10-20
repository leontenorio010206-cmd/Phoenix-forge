# Exportador visual de componentes — PhœnixForge

El entorno gráfico **Exportar a Digital** toma los nombres, direcciones y anchuras de los puertos definidos en el módulo Verilog seleccionado. No muestra pines ficticios de la placa física.

## Flujo

1. Abre o crea un proyecto Verilog en **Estudio HDL**.
2. Selecciona **Exportar a Digital** en la barra lateral y revisa el módulo y su tabla de puertos.
3. Visualiza el bloque y las conexiones sugeridas a interruptores, reloj y salidas.
4. Pulsa **Exportar componente ZIP**. Dentro van:
   - `component.v`: lógica HDL del módulo, con fuentes locales fusionadas.
   - `ports.json`: nombre, anchura y sentido de cada pin del módulo, además del SHA256.
   - `symbol.svg`: vista previa escalable del símbolo.
   - `connections.svg`: esquema gráfico ilustrativo de cableado de señales lógicas.
   - `LEEME_DIGITAL.txt`: pasos para abrirlo en Digital.
5. Descomprime el ZIP y abre **Digital de Helmut Neemann**.
6. Añade **External File / Verilog**, apunta a `component.v`, comprueba los puertos con el motor Icarus Verilog y conecta terminales de entrada y salida.
7. Guarda el circuito .dig en la misma carpeta que el archivo Verilog para facilitar su traslado.

Los diagramas **no son simulaciones**: muestran conexiones ilustrativas con el significado funcional que tú les atribuyas. El banco **Dispositivos FPGA → FPGA virtual** sí ejecuta el HDL en Icarus y produce trazas VCD.

## Alcance y compatibilidad

El paquete produce un componente Verilog externo que Digital puede utilizar cuando sus requisitos de Verilog e Icarus están instalados y el módulo es compatible. **No genera por sí mismo un .dig con conexiones automáticas ni instala el SVG como símbolo en Digital**. Digital también admite formas SVG personalizadas para determinados circuitos; eso requiere los pasos correspondientes dentro de Digital.

Sin programación de FPGA física, emulación de arquitectura/fabricante, temporización ni plugin para Tinkercad. No hay promesa de integración con una API no documentada de Autodesk.

Digital: https://github.com/hneemann/Digital

SVG personalizado: https://github.com/hneemann/Digital/discussions/1282
