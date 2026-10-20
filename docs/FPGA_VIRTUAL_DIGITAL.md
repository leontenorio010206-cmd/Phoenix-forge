# FPGA virtual y exportación de componentes para Digital

## FPGA virtual en PhœnixForge

Abre **Dispositivos FPGA → FPGA virtual · E/S**.

- Escoge un perfil del catálogo y crea o abre un proyecto Verilog.
- Selecciona el módulo principal (top). El programa extrae sus puertos de tipo `input` y `output`.
- Conecta valores 0/1 a entradas de un bit; para buses de 2 a 16 bits usa el selector numérico.
- Selecciona opcionalmente una entrada de reloj de un bit y cuántos flancos positivos quieres ejecutar.
- Pulsa **Ejecutar FPGA virtual**, autoriza únicamente HDL de confianza y revisa las salidas.
- La traza `virtual_fpga.vcd` aparece como resultado conservado y en el visor de señales de Estudio HDL.

PhœnixForge genera un testbench temporal que maneja las entradas HDL, compila el código del proyecto con Icarus, aplica el reloj y captura el resultado. **No modifica los fuentes originales ni reemplaza el compilador.**

Limitaciones iniciales: declaraciones de puertos Verilog literales (sin parámetros), máximo 40 puertos y 16 bits por entrada/salida, sin `inout`. No simula voltajes, retardos, efectos térmicos, DSP/PLL/BRAM primitivas ni pines físicos. Cada perfil de las diez FPGA utiliza el motor RTL común; **no** equivale a emular diez chips a nivel físico.

Los buses, nombres y pines que aparecen son señales HDL. La asignación a un encapsulado real requiere un chip y una placa concreta.

## Exportar a Digital

En **Archivo → Exportar componente para Digital…**, selecciona un archivo ZIP de salida. Contiene:

| Archivo | Uso |
| --- | --- |
| `component.v` | Fuente HDL fusionada en un archivo; excluye testbenches separados e integra `include` locales. |
| `ports.json` | Entradas/salidas, dirección, anchura, top, perfil FPGA y checksum SHA-256. |
| `LEEME_DIGITAL.txt` | Pasos de importación en Digital. |

Para utilizarlo: descomprime el ZIP, abre Digital, añade **External File**, selecciona el archivo Verilog e indica Icarus como simulador. Usa **Check** para validar los puertos, conéctalos a interruptores, relojes y LED y guarda el circuito de Digital junto al HDL.

Esto genera un **componente externo HDL funcional**, no un `.jar` ni una extensión instalable en Autodesk Tinkercad.

Digital original: https://github.com/hneemann/Digital

Digital sobre External File: https://github.com/hneemann/Digital/discussions/798

Digital admite además extensiones Java .jar, pero convertir HDL arbitrario a API Java requiere otra implementación y pruebas de equivalencia: https://github.com/hneemann/digitalCustomComponents

Tinkercad Circuits no ofrece actualmente una API pública documentada para instalar componentes FPGA ejecutables de terceros.

## Seguridad y alcance

El HDL de terceros puede ejecutar operaciones de archivos a través del simulador y de directivas propias del lenguaje. **No es una sandbox**. Se solicita confirmación antes de ejecutarlo; revisa el código antes de usarlo.

La exportación no pretende emular una familia FPGA entera ni generar un bitstream para programar tarjetas físicas. El archivo es reabrible en una instalación compatible de Digital con Icarus configurado; la interacción exacta depende de la versión de Digital y de la validez de los módulos Verilog.

