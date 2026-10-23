# Guion de video — Exportar HDL de PhœnixForge a Digital

**Duración estimada:** 1:45–2:30 minutos. **Formato:** tutorial académico con recreaciones vectoriales de interfaz, **no captura experimental en vivo**.  
**Autor del proyecto:** Leonardo Antonio Hernández Tenorio. **Asistencia IA:** ChatGPT (OpenAI).  
**Versión:** PhœnixForge v1.7.0.

## Secuencia y narración

| Tiempo | Pantalla / demostración | Narración sugerida |
| --- | --- | --- |
| 00:00–00:12 | Portada PhœnixForge, Digital, Icarus | «Aprenderemos a comprobar un contador de cuatro bits en PhœnixForge y exportarlo a Digital.» |
| 00:12–00:28 | Archivo → Abrir proyecto → Ejemplo .pforge | «Abrimos el proyecto de ejemplo; el diseño se llama fpga_demo y su banco de pruebas tb_fpga_demo.» |
| 00:28–00:48 | Estudio HDL, ▶ Simular, consola PASS | «Icarus Verilog ejecuta doce comprobaciones; el resultado esperado es PASS: 12 FPGA RTL vectors.» |
| 00:48–01:05 | Exportar a Digital, módulo fpga_demo, botón ZIP | «Elegimos el módulo de diseño, no el testbench, y exportamos el componente ZIP.» |
| 01:05–01:20 | Carpeta descomprimida y component.v | «Extraemos el ZIP; el archivo component.v es el que Digital puede utilizar.» |
| 01:20–01:42 | Digital → External File → Verilog; ajustes IVerilog | «En Digital vinculamos component.v y configuramos IVerilog si falta.» |
| 01:42–02:07 | Diagrama reloj/reset/bus/LED, secuencia 0000-0001-0010 | «Conectamos reloj, reset y cuatro LED; el contador avanza en cada flanco ascendente.» |
| 02:07–02:20 | Alcance real / créditos | «Esto demuestra una simulación lógica; no programa ni emula eléctricamente una FPGA real. Digital es obra de Helmut Neemann.» |

## Advertencia sobre las imágenes

Las láminas y gráficos del video son **reconstrucciones educativas** de pasos documentados en la versión v1.7.0; no sustituyen grabaciones del programa real. Para una entrega experimental, capturar en el ordenador real la consola de Icarus, el VCD y el circuito ejecutándose dentro de Digital.

## Cómo reproducir los pasos en vivo

Consulta [Tutorial de Digital](DIGITAL_TUTORIAL.md) y el [ejemplo](../examples/fpga_demo_profesor/README.md), luego realiza una grabación de pantalla propia si tu profesor exige evidencia de ejecución real.
