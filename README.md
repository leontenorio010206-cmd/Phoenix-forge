<div align="center">

<img src="app/assets/phoenix.svg" width="130" alt="PhœnixForge phoenix logo" />

# 🦅 PhœnixForge

### Forge Digital Logic

**IDE de escritorio para diseño lógico, HDL y simulación de circuitos FPGA**

![Version](https://img.shields.io/badge/version-1.1.0-f97316?style=flat-square) ![Windows](https://img.shields.io/badge/Windows-10_x64-0b71c1?style=flat-square) ![License](https://img.shields.io/badge/c%C3%B3digo-MIT-4ade80?style=flat-square)

</div>

---

## ¿Qué es PhœnixForge?

Un taller digital para crear, estudiar, simular y documentar circuitos lógicos con Verilog. La aplicación está desarrollada con **Python + Qt**, conserva proyectos en formato `.pforge` e integra un motor de simulación HDL basado en **Icarus Verilog**.

El objetivo a largo plazo es facilitar el diseño sobre diferentes modelos de FPGA y la exportación de componentes a simuladores externos, sin confundir **simulación lógica** con **programación física** de chips.

## Funciones de la v1.1

| Herramienta | Estado |
| --- | --- |
| Editor Verilog con pestañas y resaltado | Implementado |
| Proyectos `.pforge` con importación/exportación | Implementado |
| Simulador visual de reloj, contadores y semáforo | Implementado |
| Simulación HDL con Icarus y visor VCD | Implementado en fuente; pendiente validar el EXE Windows |
| Catálogo de 10 perfiles FPGA | Informativo / asignaciones de proyecto |
| Administrador de plugins y SDK | Implementación inicial |
| Exportador genérico de proyectos y fuentes | Implementado |
| Python HDL y HLS para C/C++ | Previsto, todavía no implementado |
| Programación física de FPGA | No implementada |

**El ejercicio académico de conducción fue retirado de la v1.1** a petición del autor. Se mantiene la lógica combinacional genérica y un ejemplo de sumador completo.

## Construcción automática en Windows

El flujo [Windows Build](.github/workflows/windows-release.yml) prepara Windows, Python, PySide6, PyInstaller, Icarus y los componentes necesarios. Es exclusivo de repositorios **privados**.

1. Abre la pestaña **Actions** en GitHub.
2. Selecciona **Private Windows distribution** y elige **Run workflow** (o haz un push a `main`).
3. Al finalizar, abre la ejecución y revisa **Artifacts**.
4. Descarga `PhoenixForge-v1.1.0-windows-x64` si la validación tuvo éxito. En caso contrario, descarga diagnósticos y, si se generó, el paquete **EXPERIMENTAL**.

Los ejecutables no están firmados digitalmente. No se garantiza funcionamiento hasta superar las pruebas de Windows en el flujo y, posteriormente, las de una PC Windows 10 limpia. Los artefactos tienen retención limitada; guárdalos después de descargarlos.

## Ejecutar el código desde fuentes

```bash
python -m venv .venv
# activar el entorno (en Windows: .venv\Scripts\activate)
python -m pip install -r requirements/modern.txt -r requirements/test-modern.txt
python -m app
```

Para compilar y simular Verilog desde el código fuente se necesita Icarus Verilog, o un runtime de Icarus integrado correctamente. La distribución final busca incluirlo.

## Estructura del proyecto

```text
app/         Interfaz Qt, editor, proyectos, simuladores y plugins
examples/    Sumador completo y semáforo
build/       Especificaciones de empaquetado
installer/   Instalador NSIS
vendor/      Fuentes verificadas y manifiestos de dependencias
tests/       Pruebas automatizadas
tools/       Scripts de construcción y validación
docs/        Documentación de usuario y de desarrollo
```

## Documentación y estado real

- [Guía de usuario](docs/USER_MANUAL.md)
- [Manual para desarrolladores](docs/DEVELOPER_MANUAL.md)
- [Compilación en Windows](docs/BUILD_WINDOWS.md)
- [SDK de plugins](docs/PLUGIN_SDK.md)
- [Estado y limitaciones](docs/RELEASE_STATUS.md)
- [Cambios](CHANGELOG.md)

## Atribuciones y licencia

Código propio y marca del proyecto: **MIT** (ver [LICENSE](LICENSE)). El uso y redistribución de componentes de terceros se rige por sus licencias respectivas: ver [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

> PhœnixForge es un proyecto independiente. La presencia de perfiles de terceros no implica afiliación ni certificación de los fabricantes.
