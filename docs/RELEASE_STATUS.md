# Estado de distribución — PhœnixForge 1.7.0

## Primera versión estable (criterio de CI)

La v1.7.0 es la **primera edición de PhœnixForge que pasó las pruebas estrictas de Windows** configuradas para el proyecto. Esto significa que el ejecutable real compiló en Windows Server 2022, ejecutó una suite de pruebas de código, inició su interfaz y superó pruebas del programa empaquetado con el simulador Icarus incluido.

**Última compilación aceptada verificada:** [Windows 1.7 · GitHub Actions #39528870746](https://github.com/leontenorio010206-cmd/Phoenix-forge/actions/runs/39528870746). Descarga el artefacto `PhoenixForge-Windows-v1.7-VALIDADO-CI`, que debe contener Setup.exe, Portable.exe y sumas SHA-256.

No equivale a una certificación de Windows 10/11 en hardware físico. Están pendientes pruebas de campo de consumo RAM, compatibilidad con antivirus y discos lentos, uso de placas FPGA reales y sistemas Windows 7.

## Versiones anteriores y distinción

La información de la entrega **1.1.0 experimental** en este documento quedó superada por la puerta de aceptación estricta de la v1.7.0. No deben descargarse ni presentarse como estables binarios llamados `EXPERIMENTAL`.

La versión 1.7 elimina el mecanismo de publicación de EXE experimentales cuando la aceptación falla.

## Legal, independencia y créditos

Código original MIT © Leonardo Antonio Hernández Tenorio, **cocreador y mantenedor**. Agradecemos a [Digital, de Helmut Neemann](https://github.com/hneemann/Digital) (GPLv3). Digital se utiliza como programa externo e instalación opcional; no es nuestro código ni patrocina este proyecto.

Consulta [LEGAL.md](../LEGAL.md), [CREDITS.md](../CREDITS.md), [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) y [notas de la primera estable](RELEASE_1.7.0.md).

## Publicación del repositorio

El artefacto aprobado en CI puede existir aunque el repositorio siga siendo privado. Antes de abrirlo al público debe revisarse TODO el historial Git, incluidos paquetes binarios anteriormente versionados, tal como explica [PUBLIC_RELEASE_CHECKLIST.md](PUBLIC_RELEASE_CHECKLIST.md).
