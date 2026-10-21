# PhœnixForge 1.7 — Estabilidad y control de versiones

## Estado y criterios de aceptación

**No se promete que un software tenga cero fallos ni sea compatible con cualquier laptop.**
La meta de esta versión es una puerta de aceptación reproducible:

1. Compilar en Windows Server 2022 nativo x64 con Python 3.11.9 y PySide6.
2. Ejecutar la suite completa de Python, Qt e Icarus, con **cero fallos, errores y pruebas omitidas** (sin contar la prueba del EXE aún no construido).
3. Generar un PE x64 de interfaz gráfica y verificar tamaño mínimo y checksum SHA-256.
4. Iniciar el ejecutable normal **sin Python, Qt ni Icarus en PATH**, en carpeta con espacios y Unicode.
5. Ejecutar dos veces la autoprueba empaquetada: editor, semáforo, HDL real, VCD, guardar/abrir proyecto, plugins y navegación actual, incluyendo Hardware Studio.
6. Guardar informe de tamaño, informes de Windows y evidencia JSON. El validador `release_gate.py` comprueba estos datos antes de publicar el `.exe`.

Si **cualquiera** de estas fases falla, el flujo Windows debe quedar rojo y
no publicará un `PhoenixForge-Windows-v1.7-VALIDADO-CI`. Siempre conservará
logs, trazas de error, capturas y fuentes.

Se eliminó la rama que generaba silenciosamente un EXE alternativo
`EXPERIMENTAL` cuando fallaba la validación estricta.

## Rendimiento

- El panel principal ahora usa scroll para laptops de menor resolución.
- La ventana se dimensiona según el área disponible y permite tamaño mínimo
  de 840×540 para que pueda utilizarse en equipos pequeños.
- El sondeo de USB/JTAG de Hardware Studio no corre cuando el panel está oculto.
- `tools/size_report.py` mide los tamaños del portable, runtime FPGA, fuentes
  correspondientes LGPL/GPL, licencias y aplicación. **No se eliminan componentes
  obligatorios por su licencia para aparentar una reducción de tamaño.**

La versión 1.7 no afirma una reducción cuantificada hasta medir el PE resultante
y compararlo con el artefacto previo en la misma configuración. Un `onefile`
necesita extraerse a una carpeta temporal en cada inicio y puede tardar en HDD.

## Compatibilidad real

CI Windows 2022 no equivale a una prueba de campo en Windows 10 Home/Pro,
con Windows Defender, poca RAM, pantalla 1024×600, disco duro HDD o
sistemas sin herramientas de desarrollo. Quedan pendientes las pruebas en
laptops físicas y con hardware Arduino/FPGA conectado.

**Soporte objetivo:** Windows 10/11 x64. **No certificados**: Windows 7,
Windows de 32 bits, cualquier Raspberry Pi como PC local, instalación automática
de drivers JTAG ajenos y compatibilidad universal de FPGA.

## Para descargar

1. En GitHub → Actions abre `Windows 10 x64 v1.7 (acceptance required)`.
2. Confirma que la ejecución completa esté verde y que exista
   `PhoenixForge-Windows-v1.7-VALIDADO-CI`.
3. Descarga EXE y verifica SHA256 con `dist/SHA256SUMS.txt`.
4. Guarda también `PhoenixForge-v1.7-Fuentes-y-licencias` y las notas
   de terceros para cumplir con redistribución de código.

Si no hay artefacto validado, descarga **Diagnósticos** y no sustituyas
tu ejecutable v1.6.2 que ya funciona.
