# PhœnixForge Online Setup — instalación modular verificada (prototipo)

## Qué es y qué no es

El instalador NSIS existente permite instalar **PhœnixForge** en el directorio
del usuario; incorpora dentro del ejecutable el runtime Icarus Verilog ya
verificado. No hace falta otra descarga de Icarus.

Dos componentes **opcionales, desmarcados inicialmente**, se ofrecen en el
asistente:

- **Eclipse Temurin JRE 21 x64**: runtime Java privado para Digital.
- **Digital v0.31 (GPLv3)**: simulador independiente de Helmut Neemann.

Ambas descargas se realizan desde versiones fijadas de los repositorios
oficiales y se rechazan si su tamaño y SHA-256 no coinciden con
\`installer/optional-components.json\`. Los hashes son constantes revisadas
en el código; no se obtienen sin validar desde un enlace dinámico.

El instalador requiere Internet **solo para componentes opcionales**. Si una
descarga falla, PhœnixForge sigue funcionando con el simulador Icarus
incluido. Java y Digital no se incorporan al único EXE de PhœnixForge,
lo que ahorra espacio para quienes no necesiten esos componentes.

### Integración automática

- Digital se descomprime bajo
  \`%LOCALAPPDATA%\Programs\PhoenixForge\Integrations\Digital-v0.31\`.
- Java se descomprime bajo
  \`%LOCALAPPDATA%\Programs\PhoenixForge\Integrations\Temurin-JRE21\`.
- El puente de Digital localiza automáticamente instalaciones que tengan
  recibos verificados, de modo que no hace falta buscar manualmente
  \`Digital.jar\` cuando se instaló con Setup.
- El PATH del usuario y el Java global **no se modifican**.
- Digital sigue siendo otro programa, sujeto a su propia licencia GPL.
- El usuario aún debe insertar su componente externo en Digital; la
  generación automática de un circuito \`.dig\` completo no está verificada.

### Diseño y seguridad

- Archivo NSIS: \`installer/PhoenixForge.nsi\`
- Descargador: \`installer/install_optional.ps1\`
- Manifiesto: \`installer/optional-components.json\`
- Verificador de construcción: \`tools/build_setup_windows.py\`

El descargador limita cantidad/tamaño expandido de archivos ZIP, rechaza rutas
peligrosas, evita reemplazar instalaciones ajenas y conserva recibos de
integridad. El instalador se ejecuta sin derechos de administrador.
Los drivers JTAG/Arduino **no se instalan automáticamente** porque pueden
afectar interfaces USB compartidas.

El desinstalador preserva \`Integrations\` para evitar borrar datos de terceros:
el usuario puede eliminar manualmente esas carpetas después de desinstalar.

**Importante:** al instalar por separado Digital/Java podrían fallar
componentes por conexiones interrumpidas; revisa el registro del instalador.
La instalación de runtime Java no modifica las asociaciones de archivos
del sistema operativo.

### Compilación estable

La pipeline de Windows valida el portable primero, y solo entonces compila el
Setup e incorpora ambas huellas SHA256 en \`dist/SHA256SUMS.txt\`.
No se publica el Setup si falla la aceptación nativa, el empaquetado NSIS
o la validación de scripts.

El estado \`CI accepted\` no equivale a estar probado en equipos físicos:
faltan ensayos con Windows 10 limpio, antivirus, permisos, ubicaciones Unicode,
descargas interrumpidas y reinstalación.

### Fuentes y licencias

- Digital: https://github.com/hneemann/Digital (GPLv3; versión v0.31).
- Eclipse Temurin: https://adoptium.net/ (OpenJDK GPLv2 con Classpath Exception).
- Icarus Verilog: https://github.com/steveicarus/iverilog (distribución verificada).

Se mantienen avisos y código fuente correspondiente de los componentes que
se redistribuyan; los archivos descargados provienen directamente de los
proveedores oficiales.
