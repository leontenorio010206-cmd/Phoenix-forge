# Manual de instalación — PhœnixForge v1.7.0

**Edición:** primera versión estable verificada en GitHub Actions para Windows x64  
**Autoría del proyecto:** Leonardo Antonio Hernández Tenorio (cofundador, cocreador y mantenedor)  
**Release:** https://github.com/leontenorio010206-cmd/Phoenix-forge/releases/tag/v1.7.0

## 1. Requisitos

| Elemento | Condición |
|---|---|
| Windows | Windows 10 x64 versión 1809 o posterior; Windows 11 x64 |
| Permisos | Instalación de usuario sin administrador |
| Internet | No hace falta para el núcleo; sí para Digital y Java si los seleccionas |
| Icarus Verilog | Incluido dentro del EXE completo Windows |
| Digital | Opcional, versión 0.31 desde repositorio oficial |
| Java | Opcional, Eclipse Temurin JRE 21 para usar Digital |
| Hardware FPGA | No hace falta para la simulación RTL. La programación física requiere otros controladores/herramientas. |

**No verificado:** Windows 7, sistemas x86 de 32 bits, todas las distribuciones Windows, tablets y laptops de cualquier memoria RAM. La Release pasó pruebas nativas de Windows Server 2022; no debe confundirse con una certificación universal.

## 2. Descargar desde el origen oficial

Dirígete a la [Release v1.7.0](https://github.com/leontenorio010206-cmd/Phoenix-forge/releases/tag/v1.7.0) y busca en **Assets**:

- **PhoenixForge_v1.7.0_Setup.exe** — instalación convencional, con opciones Digital/Java.
- **PhoenixForge_v1.7.0_Portable.exe** — un solo ejecutable, sin instalar Digital/Java.
- **SHA256SUMS.txt** — huellas SHA-256 de ambos ejecutables.
- **PhoenixForge_v1.7.0_Source.zip** — fuentes y avisos correspondientes.

No descargues copias de terceros, archivos de procedencia desconocida o imágenes etiquetadas «APK oficial»: la v1.7.0 publicada es para Windows x64.

## 3. Comprobar integridad (recomendado)

En PowerShell, navega a la carpeta descargada:

\`\`\`powershell
Get-FileHash .\PhoenixForge_v1.7.0_Setup.exe -Algorithm SHA256
Get-FileHash .\PhoenixForge_v1.7.0_Portable.exe -Algorithm SHA256
\`\`\`

Compara el campo \`Hash\` de cada archivo con la línea correspondiente de **SHA256SUMS.txt**. Si difiere, borra el archivo y vuelve a descargar desde GitHub. Una huella igual verifica coincidencia con el archivo publicado, **no** equivale a firma de un editor.

## 4. Instalación mediante Setup.exe

1. Ejecuta **PhoenixForge_v1.7.0_Setup.exe**.
2. Lee la bienvenida y el acuerdo MIT del código propio.
3. En **Componentes**, deja seleccionado el programa principal.
4. Si vas a importar Verilog en Digital, marca **Java Eclipse Temurin 21** y **Digital v0.31** (ambos son opcionales).
5. Elige una carpeta de instalación, normalmente \`%LOCALAPPDATA%\Programs\PhoenixForge\`.
6. Completa el asistente y abre **PhœnixForge** desde el menú Inicio.
7. En **Configuración**, verifica que las rutas manuales de Icarus (\`iverilog\`, \`vvp\`) estén vacías si deseas el motor integrado.

El asistente descarga opcionales desde GitHub en versiones fijadas; comprueba tamaño y SHA-256 antes de extraerlos. No necesita permisos de administrador ni modifica el PATH global. **No instala drivers JTAG/Arduino automáticamente.**

### Ubicación de componentes opcionales

- Digital: \`%LOCALAPPDATA%\Programs\PhoenixForge\Integrations\Digital-v0.31\`
- Temurin Java: \`%LOCALAPPDATA%\Programs\PhoenixForge\Integrations\Temurin-JRE21\`

Las carpetas contienen los archivos oficiales descomprimidos y recibos de integridad. El puente Digital puede reconocerlos automáticamente.

## 5. Uso portable

1. Coloca **PhoenixForge_v1.7.0_Portable.exe** en una carpeta con permisos de lectura y ejecución.
2. Haz doble clic para abrirlo. El primer arranque puede demorar porque PyInstaller extrae archivos temporalmente.
3. No requiere instalar Python ni Icarus; ambos forman parte del paquete Windows completo.
4. Para usar Digital con Portable necesitarás disponer de **Digital.jar** y Java por separado; el botón **Preparar y abrir Digital** te permite seleccionar Digital.jar si no encuentra una instalación compatible.

Los proyectos se guardan en tu perfil del usuario, no necesariamente al lado del EXE.

## 6. Primera prueba de funcionamiento

1. Abre el ejemplo **\`Ejemplo_Contador_FPGA_4bits.pforge\`**.
2. En **Estudio HDL**, selecciona **fpga_demo** y testbench **tb_fpga_demo**.
3. Haz clic en **▶ Simular**.
4. Confirma en la consola la salida esperada **PASS: 12 FPGA RTL vectors**.
5. Abre **Señales VCD** para examinar reloj, reset y leds.

La observación de una salida diferente exige conservar el registro y revisar el problema; no fuerces ni fabriques resultados.

## 7. Instalar Digital y Java

Si no seleccionaste los opcionales durante Setup, puedes volver a ejecutar el instalador y marcarlos, o instalar los paquetes oficiales por separado. Consulta:
- [Digital, Helmut Neemann](https://github.com/hneemann/Digital)
- [Eclipse Temurin](https://adoptium.net/)

En **Exportar a Digital → ⚡ Preparar y abrir Digital**, confirma la operación. PhœnixForge prepara su Icarus para Digital y exporta el \`component.v\` a la carpeta de usuario. Si no encuentra Digital instalado, selecciona **Digital.jar** descomprimido. Si Digital indica **Icarus no instalado**, abre **Editar → Ajustes → IVerilog** en Digital y selecciona el directorio indicado por el asistente.

**El programa no configura todos los controles de Digital ni coloca el bloque externo automáticamente.** Esa inserción se realiza en el editor de Digital; véase [tutorial](DIGITAL_TUTORIAL.md).

## 8. Solución de problemas

| Síntoma | Qué comprobar |
|---|---|
| Windows bloquea archivo desconocido | Verifica la procedencia y SHA-256. El EXE no está firmado digitalmente. No desactives el antivirus a ciegas. |
| «No se encontraron iverilog y vvp» | Usa el EXE Windows completo y deja vacías las rutas personalizadas de Configuración. |
| El instalador opcional no descarga | Revisa Internet, proxy/antivirus y vuelve a instalar opcionales desde fuente oficial. |
| No abre Digital.jar | Comprueba que Java está disponible y que no seleccionaste el ZIP en lugar del .jar. |
| Digital muestra «Icarus no instalado» | Configura **Editar → Ajustes → IVerilog** con la ruta entregada por PhœnixForge. |
| El circuito no cambia de estado | Aplica flancos ascendentes de reloj; pon reset=0 después del primer flanco de reset. |
| Pantalla con elementos pequeños | Ajusta escala de Windows; el objetivo de interfaz mínima es 840×540. |
| Proyecto viejo no abre | Respalda el archivo .pforge y consulta el registro; no borres el original. |

## 9. Actualización y desinstalación

Antes de actualizar, cierra PhœnixForge y haz respaldo de los \`.pforge\`. El instalador de usuario conserva los datos del perfil \`%LOCALAPPDATA%\PhoenixForge\`; consulta los archivos antes de borrarlos. El desinstalador deja la carpeta de integraciones opcionales para evitar eliminar datos de terceros. Si quieres borrarla, examínala antes.

## 10. Avisos y limitaciones

- PhœnixForge: [licencia MIT](../LICENSE).
- Digital: proyecto **independiente**, GPLv3 de Helmut Neemann; su uso opcional no significa afiliación.
- Icarus/Qt/Java: conservar avisos individuales; detalles en [LEGAL.md](../LEGAL.md) y [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
- La simulación RTL no genera \`.bit\`, \`.fs\`, \`.sof\` u otro firmware físico por sí misma.
- Para problemas reproducibles: https://github.com/leontenorio010206-cmd/Phoenix-forge/issues

**Material de apoyo académico para la versión pública v1.7.0.**
