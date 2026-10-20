# PhœnixForge 1.1.0 · Informe de avance y entrega de fuentes

Fecha: 12 de octubre de 2026 (UTC). Autor del proyecto: Leonardo Antonio Hernández Tenorio.

**La actualización de fuentes está implementada y probada en Linux. La entrega 1.1 NO está terminada: faltan los dos ejecutables reales y su aceptación en Windows.**

## Funciones terminadas en el código

- Refactor sobre el ZIP original 1.0; se conserva la arquitectura y la identidad gráfica. Retirada completa de la práctica combinacional específica, sus pantallas, archivos, ejemplos, exportador dedicado, imports y referencias de ayuda. Quine–McCluskey genérico permanece.
- Interfaz oscura reorganizada con editor central, diez perfiles FPGA y laboratorio secuencial visibles. Se mantienen bienvenida, iconos SVG/ICO, Acerca de, configuración y diagnósticos.
- Editor Verilog multipestaña: abrir/importar/exportar fuentes, líneas, resaltado, búsqueda, cambios, deshacer y rehacer.
- Proyectos `.pforge` esquema 1: crear, abrir, guardar, guardar como, exportar, validar integridad y conservar VCD. Prueba de continuidad de datos desde 1.0, sin modificar el esquema ni borrar archivos de proyectos antiguos.
- Icarus real con procesos sin shell, errores, timeout, cancelación y trabajo en hilo; visor digital VCD integrado.
- Relojes, contador, divisores de pulso/onda cuadrada y semáforo configurable. Conservados 13 bits para 5,208 ciclos y 26 para 50,000,000; testbench reducido de 72 ciclos.
- Sumador completo genérico con ocho vectores, SDK/API 1 de plugins, ejemplo de herramienta HDL y exportadores independientes.
- Datos persistentes en el perfil del usuario; resolución de recursos y motor incluido; exportación accesible de avisos y fuentes de componentes.

## Distribución preparada, todavía sin validar en Windows

Se implementaron PyInstaller 6.22.3 GUI onefile, icono y versión Windows, NSIS 3.11 por usuario, workflow privado `windows-2022`, compilación de Icarus 12.0 desde la fuente exacta, recogida de DLLs, fuentes/licencias y SHA-256.

El arnés empaquetado exige PE x64 GUI, tamaño mínimo razonable, arranque ordinario con ventana Win32 y dos flujos de aceptación con Icarus incluido y PATH limitado. Usa rutas con espacios y acentos. Registra explícitamente que un runner con herramientas instaladas no equivale a una VM limpia.

La fuente de Icarus y las cuatro fuentes Qt/PySide se descargaron/verificaron. Se extrajeron 162 avisos Qt originales. No se ha construido el runtime Icarus Windows ni se ha ejecutado el constructor de instaladores en este entorno.

## Pruebas realmente ejecutadas

| Verificación | Resultado |
|---|---|
| Regresión inicial del refactor | 54 aprobadas |
| Primera regresión ampliada | 64 aprobadas, 1 fallo documental detectado y corregido, 1 omitida |
| Regresión final ampliada | **65 aprobadas, 0 fallos, 1 omitida** |
| Prueba omitida | Aceptación del EXE Windows, no disponible; no se cuenta como éxito |
| Flujo integral Qt offscreen | **8/8**: recursos, ventana, editor, semáforo, HDL/VCD, guardado/reapertura, plugin y reapertura de ventana |
| Simulación real Linux | `PASS: 8` del sumador y `PASS: 72` secuenciales, VCD y detección de fallos reales |
| Limpieza del ejercicio retirado | Prueba de ausencia aprobada en código, ejemplos y documentación |
| Construcción Windows en el host disponible | **Bloqueada**, salida 1: host Linux; lista de artefactos vacía |
| GitHub | Cuenta conectada; consulta devuelve cero repositorios accesibles; no se inició ningún workflow |
| Sintaxis de distribución | Python AST 3.8, shell MSYS2, specs y YAML del workflow comprobados |

Evidencia incluida en `build/v11-tests.log`, XML, registro del fallo previo, `build/verification/`, `build/qt-sources.log` y `build/windows-build-report.json`. La revisión visual del editor y semáforo se realizó sobre las capturas Qt reales. Los dobles de pruebas de rutas no se presentan como ejecución de Icarus Windows.

## Compatibilidad comprobada y pendiente

Comprobado: Linux x64, Python 3.12.14, PySide6/Qt 6.8.3, Icarus 12.0, interfaz offscreen. No se certifican Windows 10, Windows 7, Wine ni hardware FPGA por esos resultados.

Objetivo moderno preparado: Windows 10 x64 1809+, Python 3.11.9, Qt 6.8.3 e Icarus incluidos. Windows 7 permanece experimental, separado del proceso moderno. El runner propuesto es Windows Server 2022 y no sustituye la prueba final en Windows 10 limpio.

## Bloqueo concreto para continuar

El equipo de trabajo es Linux. La ruta local de construcción se detiene para evitar producir otro binario y llamarlo Windows. GitHub está conectado, pero no hay repositorios accesibles y la integración disponible no permite crear uno. No se ha creado ni publicado un repositorio ni un artefacto remoto.

El siguiente paso es autorizar el uso del navegador para crear un repositorio **privado** `PhoenixForge`, subir el código preparado y ejecutar GitHub Actions; después, recuperar los EXE, inspeccionar los informes y corregir cualquier fallo real. El cambio de acceso al navegador requiere esa autorización. Si se facilita un repositorio privado ya accesible, puede utilizarse en su lugar.

## Archivos entregados

- `PhoenixForge_v1.1.0_Source.zip`: código, recursos, ejemplos, manuales, pruebas, scripts, workflow privado, fuentes de dependencias, evidencias y bundle de historia Git local.
- `PhoenixForge_v1.1.0_Informe.md`: copia independiente de este informe.
- `PhoenixForge_v1.1.0_SHA256SUMS.txt`: hashes de los archivos realmente generados.
- `PhoenixForge_v1.1.0_Portable.exe`: **NO generado**.
- `PhoenixForge_v1.1.0_Setup.exe`: **NO generado**.

Los hashes no certifican funcionamiento ni son firmas digitales. No se inventan hashes o tamaños para EXE ausentes.

## Ejecutar, construir y continuar

Para desarrollo: cree un entorno virtual, instale `requirements/modern.txt` y `requirements/test-modern.txt`, y ejecute `python -m app`. La simulación HDL desde fuentes necesita Icarus en ese entorno; el objetivo de la distribución autónoma es incluirlo. Esta ruta de desarrollo no sustituye al portable solicitado.

Para construir: siga `docs/BUILD_WINDOWS.md` (MSYS2/Icarus, preparación verificada, `build_windows.bat modern` o workflow privado). Para aceptación sin herramientas de desarrollo: siga `docs/COMPATIBILITY.md`. El usuario final del portable solo deberá abrir el EXE entregado; ese entregable sigue pendiente.

La historia Git local conserva la importación 1.0 y el refactor 1.1. `history/PhoenixForge.git.bundle` permite restaurarla mediante `git clone`; no incluye remotos ni credenciales. Los manuales de usuario, desarrollo, formato y SDK están en `docs/`.

## Limitaciones conocidas

- Sin arranque Windows, VM limpia, instalación/desinstalación gráfica, firma Authenticode ni compatibilidad Win7 verificados.
- El workflow y los scripts de empaquetado requieren su primera ejecución nativa; pueden necesitar ajustes según sus resultados.
- Sin síntesis, bitstreams, JTAG ni validación eléctrica de pines. Los perfiles generales no sustituyen un chip concreto.
- Sin traducción general Python/C++/VHDL a hardware, ni exportador Digital genérico. Digital/GTKWave son externos opcionales.
- El visor VCD tiene límites de tamaño/señales/eventos documentados. El parser de puertos no elabora todo SystemVerilog.
- Los plugins de otros tipos tienen contratos y registro, pero requieren adaptadores adicionales de UI. Los plugins se ejecutan con permisos del usuario tras aceptación.
- Los requisitos Python/Qt/Icarus están fijados; la imagen hospedada y MSYS2 evolucionan. Se conservan inventarios, sin prometer reproducción binaria idéntica.
