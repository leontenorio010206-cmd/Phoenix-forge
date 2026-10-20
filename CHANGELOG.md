## 1.4.0 — Exportador visual para Digital
- Pantalla integrada Qt para visualizar el bloque Verilog, pines HDL y diagramas de conexiones.
- Símbolo SVG y esquema SVG generados automáticamente desde el módulo real del proyecto.
- Tabla de puertos, exportación ZIP funcional y acceso al banco FPGA virtual.
- Guía explícita para Digital External File, sin prometer generación automática de .dig ni plugins Tinkercad.
- Pruebas GUI, de XML SVG y de integridad del paquete de exportación.

## 1.3.0 — FPGA virtual y exportación para Digital
- Banco interactivo de señales HDL con testbench generado, reloj manual, entradas de 1 a 16 bits y trazas VCD.
- Integración del motor Icarus con los diez perfiles FPGA a nivel RTL funcional.
- Paquete de componentes Verilog para Digital External File, con puertos, fuentes fusionadas y guía de importación.
- Pruebas reales de ejecución de sumador, contador y controles de GUI.
- No incluye emulación física, bitstreams/JTAG, Tinkercad plugin ni extensión Java JAR.

## 1.2.0 — Perfiles RTL y proyectos de muestra (en desarrollo)
- Semáforo y divisores disponibles como proyectos de muestra en lugar de pantalla fija.
- Demos autoverificables de contador RTL para los 10 perfiles FPGA.
- Botones de simulación RTL por perfil; no modela tiempos, silicio ni programación física.
- Pruebas de regresión para los diez perfiles; compatibilidad Windows pendiente de comprobar en el nuevo paquete.

# Historial

## 1.1.0 — 2026-10-12 · candidato, distribución Windows pendiente

- Retirada la práctica combinacional específica y sus pantallas, plantillas, pruebas y exportador dedicado.
- Conservado Quine–McCluskey como motor independiente; añadido sumador completo de un bit con testbench exhaustivo.
- Reorganizada navegación: editor HDL, perfiles FPGA y laboratorio secuencial como accesos principales.
- Conservados los contenedores esquema 1, plugins API 1, VCD, semáforo y exportación genérica.
- Separados recursos de extracción del EXE, proyectos y ajustes persistentes del perfil de usuario.
- Resolución de Icarus integrado con rutas absolutas calculadas en ejecución y PATH limitado al proceso hijo.
- Añadidos construcción desde fuente de Icarus 12.0, inventario de dependencias, licencias, verificaciones PE y SHA-256.
- Preparados portable GUI onefile con PyInstaller 6.22.3 e instalador NSIS por usuario.
- Añadidos workflow Windows privado, aceptación nativa empaquetada, arranque ordinario, dos pruebas integrales y rutas Unicode.
- Añadida exportación accesible de licencias y fuentes de componentes desde Ayuda.
- Actualizados pruebas, manuales y seguimiento de limitaciones; no se declara soporte Windows sin ejecución nativa.

## 1.0.0 — 2026-10-09

Base importada del ZIP original, conservada en la etiqueta Git local `v1.0.0`.
Aplicación Qt, editor HDL, formato .pforge esquema 1, Icarus, VCD, modelos secuenciales,
Quine–McCluskey, diez perfiles FPGA, plugins API 1 y exportación de proyectos.
La historia Git conserva el origen del refactor; el árbol y la distribución 1.1 contienen solo las funciones vigentes.
