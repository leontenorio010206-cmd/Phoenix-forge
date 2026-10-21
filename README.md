<div align="center">

<img src="app/assets/phoenix.svg" width="130" alt="PhœnixForge phoenix logo" />

# 🦅 PhœnixForge

### Forge Digital Logic

**IDE de escritorio para diseño lógico, HDL y simulación de circuitos FPGA**

![Version](https://img.shields.io/badge/v1.7.0-Primera_estable_para_Windows_x64-20a774?style=flat-square) ![Windows](https://img.shields.io/badge/Windows-10_x64-0b71c1?style=flat-square) ![License](https://img.shields.io/badge/c%C3%B3digo-MIT-4ade80?style=flat-square)

</div>

---

## ¿Qué es PhœnixForge?

Un taller digital para crear, estudiar, simular y documentar circuitos lógicos con Verilog. **PhœnixForge 1.7.0 es la primera edición estable según sus pruebas automatizadas de Windows 10/11 x64**. Su ejecutable y Setup aprobaron la aceptación nativa de GitHub Actions; no se ha certificado el funcionamiento en todas las laptops y no se promete ausencia absoluta de errores. La aplicación está desarrollada con **Python + Qt**, conserva proyectos en formato `.pforge` e integra un motor de simulación HDL basado en **Icarus Verilog**.

El objetivo a largo plazo es facilitar el diseño sobre diferentes modelos de FPGA y la exportación de componentes a simuladores externos, sin confundir **simulación lógica** con **programación física** de chips.

## Funciones de PhœnixForge

| Herramienta | Estado |
| --- | --- |
| Editor Verilog con pestañas y resaltado | Implementado |
| Proyectos `.pforge` con importación/exportación | Implementado |
| Simulador visual de reloj, contadores y semáforo | Implementado |
| Simulación HDL con Icarus y visor VCD | Implementado y aceptado automáticamente en Windows x64 |
| Catálogo de 10 perfiles FPGA | Informativo / asignaciones de proyecto |
| Administrador de plugins y SDK | Implementación inicial |
| Exportador genérico de proyectos y fuentes | Implementado |
| Python HDL y HLS para C/C++ | Previsto, todavía no implementado |
| Diagnóstico USB/JTAG de FPGA y herramientas externas | Implementación asistida; hardware físico no certificado |

**El ejercicio académico de conducción fue retirado de la v1.1** a petición del autor. Se mantiene la lógica combinacional genérica y un ejemplo de sumador completo.

## Construcción automática en Windows

El flujo [Windows Build](.github/workflows/ci-windows.yml) prepara Windows, Python, PySide6, PyInstaller, Icarus y los componentes necesarios. Solo publica el ejecutable cuando pasa la aceptación nativa. El paquete del Setup añade Digital y Java como **descargas oficiales opcionales**, verificadas por SHA-256.

1. Abre [la última compilación v1.7 que aprobó Windows](https://github.com/leontenorio010206-cmd/Phoenix-forge/actions/runs/39528870746).
2. En **Artifacts** descarga `PhoenixForge-Windows-v1.7-VALIDADO-CI` (GitHub puede pedirte iniciar sesión).
3. Descomprime y ejecuta `PhoenixForge_v1.7.0_Setup.exe`, o usa `PhoenixForge_v1.7.0_Portable.exe` sin instalación.
4. En el Setup podrás seleccionar opcionalmente **Digital v0.31** y **Java Temurin 21**; se descargan de fuentes oficiales, solo con Internet. El núcleo ya incluye Icarus.
5. Revisa `SHA256SUMS.txt` y los avisos de terceros. Si falla una compilación posterior, usa la última ejecución exitosa.

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

## Cocreador, créditos y licencias

**Cocreador y mantenedor del proyecto:** **Leonardo Antonio Hernández Tenorio** ([@leontenorio010206-cmd](https://github.com/leontenorio010206-cmd)).

Gracias a **Helmut Neemann** por desarrollar [**Digital**](https://github.com/hneemann/Digital), simulador educativo de circuitos bajo **GNU GPLv3**. PhœnixForge se integra de manera **independiente** con Digital mediante archivos Verilog y lanzamiento externo; el Setup puede descargarlo opcionalmente desde GitHub. Este agradecimiento **no implica colaboración ni patrocinio oficial** de Digital.

Nuestro código original está bajo **MIT** ([LICENSE](LICENSE)); Digital, Icarus, Qt y otros paquetes **conservan sus propias licencias y derechos**. Consulta [CREDITS.md](CREDITS.md), [LEGAL.md](LEGAL.md) y [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). La distribución no está firmada por Microsoft y no incluye aprobación de fabricantes de FPGA.

## Estado público de la primera estable

**Versión 1.7.0 — primera estable para Windows x64 (aceptada por CI).** Incluye editor HDL, simulación Verilog real, ejemplos, banco virtual de señales, visor VCD, administrador de plugins, Hardware Studio y Setup con Digital/Java opcionales. La simulación RTL **no** equivale a emulación exacta del chip FPGA ni a validación de programación de placas reales.

- [Notas de la primera edición estable](docs/RELEASE_1.7.0.md)
- [Seguridad y limitaciones](SECURITY.md)
- [Preparación para publicación pública](docs/PUBLIC_RELEASE_CHECKLIST.md)

## Estado de calidad v1.7

- **CI Windows obligatorio**: pruebas de código + dos autopruebas del EXE sin Python ni Icarus en PATH + arranque gráfico + reporte de checksum.
- El ejecutable no se publica como validado si falla una etapa. **Validado en CI no es certificado en una PC limpia**; faltan pruebas en laptops reales, incluyendo poca RAM y discos mecánicos.
- Se incluyen diagnósticos y mediciones de tamaño para comparar versiones sin eliminar Icarus, Qt ni fuentes/licencias correspondientes.
- Windows 7, Windows x86 de 32 bits y chips o cables FPGA no validados permanecen fuera de la compatibilidad garantizada.
- Consulta [Estado de la versión 1.7](docs/STABILITY_170.md).
