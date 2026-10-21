# PhœnixForge Android · 0.1 alpha

**Estatus: port experimental**, no equivale a la Release estable para Windows 1.7.0.

## Qué funciona en la primera APK

- Interfaz táctil nativa y ligera, sin root y sin permisos de almacenamiento peligrosos.
- Abrir archivos `.pforge` del escritorio usando el selector de documentos de Android.
- Editar fuentes Verilog y SystemVerilog (`.v`, `.sv`) entre los módulos de un proyecto.
- Añadir archivos HDL, ver resumen básico de módulos (no es un parser HDL completo).
- Guardar archivos `.pforge` compatibles con el formato ZIP + `manifest.json` de la edición de escritorio.
- Comprobar SHA-256 de todos los archivos importados y conservar el identificador del proyecto,
  metadatos, asignación de pines y artefactos binarios originales al guardar.
- Archivos de hasta 32 MiB y 512 entradas, con validación de nombres y rutas. No se ejecuta
  código importado.

## Qué no funciona aún

**No hay motor Icarus Verilog compilado para Android** dentro de esta APK. No simula
el silicio de las FPGA, no genera bitstreams, no configura drivers USB/JTAG, no
instala ni ejecuta Digital.jar y no abre plugins de escritorio.

Android no ejecuta `.exe` de Windows. Esta interfaz Java nativa utiliza el modelo
de documento Android para importación/exportación y se adaptará a simulación local
en una fase posterior, con runtime Icarus para Android compilado legalmente y probado.
No se usa Termux ni Winlator como dependencia.

## Cómo compilar (Linux/macOS/Windows)

Instalar JDK 17, Android SDK 35 y Gradle 8.10.2:

```sh
cd android
gradle --no-daemon :app:testDebugUnitTest :app:assembleDebug
```

El APK de pruebas aparecerá en:
`android/app/build/outputs/apk/debug/app-debug.apk`.

La rama `feature/android-port` ejecuta CI Android nativo en GitHub Actions,
corre pruebas de compatibilidad de `.pforge` y genera un **APK debug**.
El archivo está firmado con una clave de depuración, por lo que **no** es un
paquete para Play Store, ni una certificación de estabilidad o seguridad.
Instalar solamente si se aceptan las limitaciones de esta vista previa.

## Licencias

Código original MIT, copyright 2026 Leonardo Antonio Hernández Tenorio.
El APK no contiene Icarus, Java Temurin externo ni Digital de Helmut Neemann;
por tanto no suplanta sus licencias. Digital conserva GPLv3.

La meta posterior es llevar a Android un núcleo HDL compartido mediante una
interfaz de simulación desacoplada, con pruebas de rendimiento en arm64 y permisos
de acceso USB solo para casos de uso explícitos.
