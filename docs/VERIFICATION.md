# Registro de verificación · 1.1.0

Actualización y repetición: 12 de octubre de 2026 (UTC). La evidencia local corresponde a Linux x64, Python 3.12.14, PySide6/Qt 6.8.3 e Icarus 12.0.

## Registro de ejecuciones

- Regresión tras el refactor inicial: 54 pruebas aprobadas, sin omisiones.
- Primera regresión ampliada: 64 aprobadas, 1 fallo y 1 omitida. La comprobación de limpieza detectó que este registro todavía contenía documentación del ejercicio retirado. Se sustituyó el registro desactualizado; se conserva el log de ese fallo en `build/v11-tests-before-doc-fix.log`.
- Regresión final: **65 aprobadas, 0 fallos, 1 omitida**, 2.48 s. La omitida exige el ejecutable Windows no disponible. Evidencia: `build/v11-tests.log` y `build/v11-tests.xml`.
- Flujo integral repetido tras los cambios: **8/8 comprobaciones aprobadas**, Qt real offscreen, Icarus, `PASS: 72`, VCD y guardado/reapertura; 8 eventos de latido mientras trabajaba el motor. Evidencia: `build/verification/acceptance.json`, `simulation.log`, capturas y `Acceptance.pforge`. No es una prueba Windows.
- Fuentes Qt/PySide: cuatro archivos descargados, SHA-256 contrastado y 162 avisos originales extraídos.
- Intento del constructor Windows en este host: bloqueado explícitamente por plataforma Linux; código de salida 1, `artifacts: []`. Evidencia en `build/windows-build-report.json`.

La prueba empaquetada se omite por ausencia del EXE. La omisión no es éxito. No se han ejecutado pruebas Windows, instalador, VM limpia ni FPGA físico.

## Cobertura

Se verifican proyectos/esquemas, integridad y rechazo de rutas, perfiles, simplificación de todas las funciones de tres variables y casos de cuatro, contadores, divisor de pulsos y de onda cuadrada, semáforo, Icarus real y fallos de proceso, exportación, plugins y flujo Qt.

La ampliación cubre separación entre recursos temporales y datos persistentes, resolución del compilador integrado y su entorno hijo, continuidad de proyectos 1.0, rechazo de ejecutables inválidos, corrupción de dependencias, ausencia del ejercicio retirado y exportación de fuentes/licencias.

Las pruebas de comandos con dobles verifican argumentos y errores, no ejecución real de un compilador Windows. Los tests `hdl` y el flujo integral usan el Icarus real disponible en Linux.

## Aceptación pendiente

EXE real, arranque nativo, bibliotecas empaquetadas, Icarus Windows, rutas Unicode bajo Windows, doble ejecución, instalación/desinstalación gráfica y Windows 10 limpio. El workflow preparado no ha sido ejecutado. Digital genérico, síntesis/JTAG, HDL/HLS avanzado y validación eléctrica no están implementados.

También se comprobaron sintaxis Python compatible con 3.8 mediante AST (no ejecución 3.8), sintaxis del shell MSYS2, `.spec` y ausencia de errores de whitespace Git. La inspección visual de las capturas del editor y semáforo corresponde a Linux offscreen.
