# PhœnixForge v1.5 — Preparar y abrir Digital

## Problema que resuelve
Digital (de Helmut Neemann) muestra un error de IVerilog si no encuentra
`iverilog.exe`. Además, el componente **Archivo externo** no acepta archivos ZIP
ni proyectos `.pforge`: requiere un archivo Verilog real.

La v1.5 añade **Exportar a Digital → Preparar y abrir Digital**:

1. Si es la primera vez, elige `Digital.jar` de tu copia **ya descomprimida**.
2. Confirma que quieres preparar el componente y abrir la aplicación externa.
3. PhœnixForge comprueba con SHA256 el motor Icarus integrado y copia una
   distribución x64 completa a su carpeta de datos de usuario.
4. Crea `component.v`, `ports.json` y los SVG directamente en una carpeta fija.
5. Inicia Digital con la carpeta `bin` de Icarus en el PATH **del proceso**,
   sin editar la variable PATH global.
6. Copia al portapapeles la etiqueta, entradas, salidas y ruta exacta de Icarus.

**Si Digital aún dice «Icarus no instalado»** (porque tiene su propio campo
IVerilog): entra una sola vez a **Editar → Ajustes / Configuración → IVerilog**
y selecciona la carpeta Icarus que PhœnixForge indica. Algunos ajustes
de Digital no usan el PATH del proceso. La v1.5 no modifica la configuración
externa sin consentimiento ni realiza automatización oculta de clics.

### Insertar el componente en Digital

**Componentes → Varios → VHDL/Verilog → Archivo externo**. Doble clic en el
rectángulo, selecciona **Aplicación = IVerilog** y en **Código del programa**
elige el **`component.v`** de la carpeta que se muestra (NO el ZIP).
Los campos `Etiqueta`, `Entradas` y `Salidas` pueden copiarse directamente
desde PhœnixForge. Verifica con el botón **Comprobar** y luego conecta pines.

### Lo que sí se automatiza

- Copia del **Icarus integrado**, sin descargar ni instalar compiladores.
- Verificación SHA256 de la distribución.
- Exportación lista para selección inmediata en Digital (sin descomprimir).
- Descubrimiento y apertura de tu `Digital.jar`.
- Puertos extraídos del módulo HDL, no escritos manualmente por la app.
- Configuración Icarus disponible para el proceso Digital y datos copiados.

### Lo que todavía no se automatiza

- No se descarga Java ni Digital; necesitas tenerlos instalados/extraídos.
- No se edita la configuración `.digital.cfg` de Digital.
- No se inserta silenciosamente un componente en un circuito abierto ni
  se genera un archivo `.dig` no validado.
- No es emulación de FPGA física, JTAG ni extensión de Tinkercad.

### Ubicación en Windows

De forma predeterminada usa:

`%LOCALAPPDATA%\PhoenixForge\digital\icarus`

`%LOCALAPPDATA%\PhoenixForge\digital\components\PF_<top>\component.v`

No necesita permisos de administrador. Nunca modifica automáticamente
el directorio de instalación de Digital.

### Seguridad

El código Verilog puede ejecutar instrucciones al simularse. La aplicación
pide consentimiento antes de preparar el puente. Ejecuta HDL y JAR de
fuentes confiables. Si una carpeta exportada contiene archivos
que no son de PhœnixForge, se detiene sin borrarlos.
