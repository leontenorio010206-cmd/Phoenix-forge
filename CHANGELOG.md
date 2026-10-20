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
