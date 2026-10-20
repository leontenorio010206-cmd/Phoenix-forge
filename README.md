<div align="center">

<img src="app/assets/phoenix.svg" width="130" alt="PhœnixForge phoenix logo" />

# 🦅 PhœnixForge

### Forge Digital Logic

**IDE de escritorio para diseño lógico, HDL y simulación de circuitos FPGA**

![Version](https://img.shields.io/badge/version-1.7.0-f97316?style=flat-square) ![Windows](https://img.shields.io/badge/Windows-10_x64-0b71c1?style=flat-square) ![License](https://img.shields.io/badge/c%C3%B3digo-MIT-4ade80?style=flat-square)

</div>

---

## ¿Qué es PhœnixForge?

Un taller digital para crear, estudiar, simular y documentar circuitos lógicos con Verilog. La versión 1.7 busca mejorar la estabilidad en Windows 10/11 x64; no puede garantizar cero fallos en todos los equipos. La aplicación está desarrollada con **Python + Qt**, conserva proyectos en formato `.pforge` e integra un motor de simulación HDL basado en **Icarus Verilog**.

El objetivo a largo plazo es facilitar el diseño sobre diferentes modelos de FPGA y la exportación de componentes a simuladores externos, sin confundir **simulación lógica** con **programación física** de chips.

## Funciones de PhœnixForge

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

El flujo [Windows Build](.github/workflows/ci-windows.yml) prepara Windows, Python, PySide6, PyInstaller, Icarus y los componentes necesarios. Es exclusivo de repositorios **privados**.

1. Abre la pestaña **Actions** en GitHub.
2. Selecciona **Windows 10 x64 v1.7** y elige **Run workflow** (o haz un push a `main`).
3. Al finalizar, abre la ejecución y revisa **Artifacts**.
4. Descarga `PhoenixForge-Windows-v1.7-VALIDADO-CI` **solo cuando las pruebas nativas pasen**. Si falla la aceptación no se publica EXE; solo diagnósticos y fuentes.

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

## Próxima actualización: proyectos de muestra y perfiles RTL

La rama de desarrollo `feature/fpga-rtl-examples` organiza el semáforo/divisores y el sumador bajo **Proyectos de muestra**. Desde **Dispositivos FPGA** permite crear y simular un contador RTL autoverificable en cualquiera de los diez perfiles. Consulta [alcance y límites](docs/RTL_PROFILES.md). La simulación RTL no implica emulación física ni programación de cada chip.

## Estado de calidad v1.7

- **CI Windows obligatorio**: pruebas de código + dos autopruebas del EXE sin Python ni Icarus en PATH + arranque gráfico + reporte de checksum.
- El ejecutable no se publica como validado si falla una etapa. **Validado en CI no es certificado en una PC limpia**; faltan pruebas en laptops reales, incluyendo poca RAM y discos mecánicos.
- Se incluyen diagnósticos y mediciones de tamaño para comparar versiones sin eliminar Icarus, Qt ni fuentes/licencias correspondientes.
- Windows 7, Windows x86 de 32 bits y chips o cables FPGA no validados permanecen fuera de la compatibilidad garantizada.
- Consulta [Estado de la versión 1.7](docs/STABILITY_170.md).
