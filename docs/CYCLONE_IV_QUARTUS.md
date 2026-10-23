# Cyclone IV con Quartus Prime Lite — puente inicial

**Función incorporada en rama de desarrollo, posterior a v1.7.0.**
PhœnixForge prepara proyectos **.qpf/.qsf** y permite compilarlos mediante
el ejecutable oficial `quartus_sh`. **No programa chips, no descubre el número
exacto del FPGA por USB y no instala Quartus ni drivers.**

## Qué necesitas

- Quartus Prime Lite o Standard con **paquete de soporte Cyclone IV** instalado.
  Descarga oficial (Lite 25.1 para Windows):
  https://www.altera.com/downloads/fpga-development-tools/quartus-prime-lite-edition-design-software-version-25-1-windows
- El **part number completo** impreso sobre tu chip, por ejemplo
  `EP4CE6E22C8N`. Este es un ejemplo de formato, **no** el valor de tu placa.
- Para conectar LEDs, reloj, botones o memorias de la placa:
  esquema oficial **del modelo exacto** y asignaciones de pines verificadas.
  El USB-Blaster identifica el adaptador JTAG, no garantiza el modelo del FPGA.

## Pasos

1. Abre tu proyecto `.pforge` y comprueba que el módulo principal es
   sintetizable; no selecciones el testbench.
2. En **Hardware Studio → Cyclone IV / Quartus** escribe el código completo
   que aparece en el chip y el módulo principal Verilog.
3. Pulsa **Generar proyecto Quartus** y escoge la carpeta de salida. Se crea
   una carpeta nueva (sin sobrescribir otra existente) con fuentes de diseño,
   `.qpf`, `.qsf` y un archivo de precauciones.
4. Abre el `.qpf` desde Quartus Prime para confirmar que reconoce el part.
   Si no, instala el paquete de dispositivos Cyclone IV o revisa el código.
5. Opcional: selecciona `quartus_sh.exe` de la instalación oficial y pulsa
   **Compilar con Quartus**. La compilación es externa y no toca el USB/JTAG.
6. **No programes el hardware** hasta validar el pinout completo, frecuencia
   y restricciones de reloj, estándar/voltajes I/O, y lectura JTAG del chip.

Si la computadora tiene Quartus en el `PATH` no necesitas seleccionar el EXE.
Para una compilación manual desde la carpeta exportada puedes utilizar:

```powershell
quartus_sh --flow compile PhoenixForge_CycloneIV
```

## Seguridad y limitaciones

- Se valida la **forma** del part number `EP4CE...` o `EP4CGX...`.
  La lista real de chips la valida Quartus; no hay compatibilidad certificada
  con tarjetas físicas ni garantía de que soporte todos los chips.
- La interfaz **no exporta pines por defecto**. Si marcas explícitamente
  «Incluir pines», incorpora los de `Project.pins` que tengan formato
  `PIN_...`. **Nunca se infieren**; verifica todos antes de activar la opción.
  Un número de pin válido sintácticamente no implica que sea correcto.
- No se configuran automáticamente restricciones de reloj (`.sdc`), PLL,
  estándares de voltaje, memorias externas ni periféricos de la placa.
- Las fuentes designadas exclusivamente como testbench se excluyen
  automáticamente de la exportación.
- Si Quartus genera un archivo `.sof` después de compilar, **no significa**
  que esté listo para cargar en una placa desconocida.
- La versión estable v1.7.0 publicada anteriormente no contiene este puente:
  compila esta rama o espera a incluirla en una nueva versión validada.
- No se ha probado con Quartus ni con una Cyclone IV física desde GitHub CI.

Referencias:
- [Soporte y descarga Quartus Lite 25.1](https://www.altera.com/downloads/fpga-development-tools/quartus-prime-lite-edition-design-software-version-25-1-windows)
- [Quartus y automatización por línea de comandos](https://www.intel.com/content/www/us/en/docs/programmable/683432/22-4/compilation-with-quartus-sh-flow.html)
