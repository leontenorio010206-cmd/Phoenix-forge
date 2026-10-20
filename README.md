# 🦅 PhœnixForge

**Forge Digital Logic** · Entorno de escritorio para diseño digital, Verilog y proyectos FPGA.

> **Estado:** repositorio privado inicializado. La versión 1.1.0 está preparada para importar desde el paquete original `PhoenixForge_GitHub.git.bundle`. La versión Windows todavía **no está verificada**.

## Funciones de la versión 1.1.0
- Editor HDL con pestañas y proyectos `.pforge`.
- Simulador educativo de relojes, contadores y semáforo.
- Catálogo de diez perfiles de FPGA.
- Simulación de Verilog mediante Icarus (pendiente verificar en Windows empaquetado).
- SDK inicial de plugins y exportación de archivos.
- Ejercicio académico del carrito retirado según lo solicitado.

**Importante:** no simula físicamente el silicio ni permite programar tarjetas FPGA por USB/JTAG. La conversión de Python o C++ a lógica FPGA no está implementada.

## Compilación automática en GitHub

El flujo **PhoenixForge · Compilación Windows** creará un artefacto experimental o verificado según las pruebas.

El código fuente se importa mediante el archivo `PhoenixForge_GitHub.git.bundle` (paquete Git de 1.1.0), que debe colocarse en la raíz del repositorio. Esta etapa conserva el historial y evita instalar herramientas de desarrollo en la laptop.

**Cuando exista el bundle:** abre [Actions](../../actions), selecciona el flujo de Windows y consulta los resultados. El EXE final se entrega como artifact en la ejecución, no mediante un link inventado.

## Desarrollo, seguridad y licencias

El objetivo de la v1.1 es Windows 10 x64. La compatibilidad Windows 7 sigue siendo experimental. Se deben validar las licencias de los binarios y dependencias redistribuidos. Este repositorio es privado para evitar publicar trabajo incompleto.

Sin garantía de funcionamiento hasta pasar las pruebas integrales de Windows.
