# Simulación RTL en diez perfiles FPGA

En PhœnixForge los diez perfiles pueden utilizar el **mismo motor Icarus Verilog** para diseños RTL independientes del fabricante. Selecciona **Dispositivos FPGA → Crear demo RTL para esta FPGA → F5**. El ejemplo conserva el ID del perfil y ejecuta un contador Verilog con testbench real y doce vectores autoverificables.

Usa **Simular proyecto con este perfil** para simular las fuentes de tu proyecto actual (con confirmación). En **Proyectos de muestra** quedan el semáforo y sus divisores, el sumador y el contador RTL; el laboratorio animado deja de ocupar una página fija.

## Limitaciones

Los perfiles de familia no designan un chip concreto. **Simulación funcional RTL no significa emulación física de las diez tarjetas**. Este motor no modela LUT físicas, PLL, IP del fabricante, retardos, consumo, recursos específicos, pines de placa ni programación JTAG. Los pines guardados en proyectos son metadatos. Para síntesis, tiempos y programación hace falta seleccionar un dispositivo, encapsulado y herramientas de fabricante o una cadena compatible.

Las pruebas comprueban que las diez selecciones ejecuten el mismo circuito RTL y generan VCD; **no prueban diez arquitecturas de hardware distintas**.
