# Manual de usuario — PhœnixForge 1.1.0

## Distribución y primer inicio

**Estado del candidato:** los ejecutables Windows aún no están construidos ni verificados en el informe de esta entrega. Este manual describe el uso previsto del paquete generado por el proceso de distribución; el ZIP de fuentes no sustituye al portable.

Cuando se entregue `PhoenixForge_v1.1.0_Portable.exe`, cópialo a una carpeta de tu usuario y ábrelo con doble clic. El paquete está preparado para incluir Python, Qt e Icarus. No hay descargas durante el arranque ni configuración de PATH. La extracción temporal de recursos no guarda tus proyectos.

El instalador adicional `PhoenixForge_v1.1.0_Setup.exe` está preparado para instalar por usuario, crear entrada de Inicio y ofrecer acceso de escritorio. La desinstalación conserva `%LOCALAPPDATA%\PhoenixForge` y los proyectos guardados en otras carpetas. La instalación real sigue pendiente de prueba.

Inicio es la bienvenida. El editor está en Estudio HDL; los perfiles y el laboratorio secuencial tienen accesos propios. Los paneles del editor son redimensionables. Para desarrollo desde fuentes consulta `DEVELOPER_MANUAL.md`.

## Proyectos y fuentes

**Archivo → Nuevo proyecto** crea un módulo Verilog mínimo. **Abrir proyecto** carga un `.pforge`, comprueba sus rutas, estructura y hashes, y rechaza un contenedor corrupto. **Guardar proyecto** conserva también los resultados de simulación. Guardar sobre un archivo existente solicita confirmación; **Guardar como** crea otra copia.

Los documentos abiertos son buffers del proyecto: sus cambios se guardan en memoria inmediatamente y el título muestra `*` hasta guardar el contenedor. Cerrar una pestaña no elimina el archivo ni descarta su texto. Cerrar la app o sustituir el proyecto con cambios pendientes ofrece guardar, descartar o cancelar.

**+ Archivo** admite una ruta relativa, por ejemplo `rtl/control.v`. **Importar** incorpora texto UTF-8 al proyecto. Python, C/C++, VHDL y cabeceras se conservan como fuentes; la importación no los ejecuta ni los convierte. Los archivos `.v` y `.sv` se entregan a Icarus; `.vh` y `.svh` sirven como cabeceras incluidas.

**Guardar archivo fuente como** exporta el archivo de la pestaña activa de forma independiente. Guardarlo así no sustituye el guardado del proyecto.

| Atajo | Acción |
|---|---|
| Ctrl+N / Ctrl+O | Crear / abrir proyecto |
| Ctrl+S / Ctrl+Shift+S | Guardar proyecto / guardar como |
| Ctrl+I | Importar fuentes |
| Ctrl+Alt+S | Exportar archivo activo |
| Ctrl+F | Buscar texto en el archivo activo |
| Ctrl+Z / Ctrl+Y | Deshacer / rehacer |
| F5 / Shift+F5 | Compilar y simular / detener |

## Icarus Verilog

En la distribución autónoma, deja vacías las rutas de `iverilog` y `vvp` en **Configuración** para seleccionar ambos componentes incluidos. La pantalla Inicio indica si se detecta el motor integrado. Una ruta personalizada selecciona una instalación avanzada externa y no modifica el PATH del sistema.

En ejecución desde fuentes se puede usar un Icarus instalado por el desarrollador. Si falta, la aplicación informa del error y no presenta una compilación exitosa. Los modelos internos de relojes y semáforo siguen disponibles.

Para simular, abre todos los módulos necesarios, elige el módulo principal y selecciona explícitamente el testbench. Si el campo testbench está vacío se usa el módulo principal como raíz. **↻ Módulos** vuelve a indexar los nombres después de editar o importar. La indexación es ligera; el compilador es quien valida la sintaxis real.

El testbench debe terminar, normalmente mediante `$finish`. Para generar trazas incluye:

```verilog
initial begin
    $dumpfile("resultado.vcd");
    $dumpvars(0, tb);
    // estímulos y comprobaciones
    #100;
    $finish;
end
```

El motor ejecuta `iverilog -g2012 -Wall -s RAIZ ...` y luego `vvp -N ...` con listas de argumentos y sin shell. `$fatal`, una compilación fallida, `$stop`, un tiempo agotado o una cancelación no se presentan como éxito. Un código 0 significa que el proceso terminó correctamente; para demostrar corrección funcional el testbench debe contener comprobaciones, como los ejemplos incluidos.

La ejecución se realiza en un hilo de trabajo, con una copia de las fuentes. Puedes seguir usando la interfaz. Si editas las fuentes durante la ejecución, la consola advierte que los resultados corresponden a la copia anterior y el registro contiene sus hashes.

El tiempo máximo se configura entre 1 y 120 segundos por proceso. La consola conserva hasta 2 MiB por log, y los VCD hasta 24 MiB. **Detener** cancela el proceso; la cancelación del árbol de procesos debe probarse además en Windows.

Las simulaciones no son una sandbox de seguridad: las operaciones de archivo de Verilog se ejecutan con los permisos de tu cuenta. La app solicita aceptación antes de lanzarlas. Importar una fuente no la ejecuta.

## Resultados y señales

Los errores con archivo y línea aparecen en **Errores y advertencias**. Haz doble clic para abrir esa línea. Los diagnósticos que no incluyen localización siguen visibles en la consola.

En el explorador, haz doble clic en un `.vcd` conservado para abrirlo. El visor muestra valores digitales y buses, incluye zoom, desplazamiento y un cursor con tiempo. Los números del eje se multiplican por la unidad indicada en la cabecera. Un bus se muestra en hexadecimal; X/Z se distinguen con otro color.

Límites del visor: 24 MiB, 256 señales, 200 000 cambios y anchuras de hasta 4096 bits. Se admiten VCD digitales escalares/binarios; señales reales, cadenas y extensiones de otros formatos no se representan. Para trazas mayores o análisis avanzado configura GTKWave y usa **Simulación → Abrir último VCD en GTKWave**.

El contenedor distingue `icarus/latest/` para los logs recientes y `icarus/last_success/` para la última traza que terminó correctamente. Una compilación fallida conserva ese VCD anterior: no debe interpretarse como resultado de la ejecución fallida. Las trazas internas tienen prefijos `internal_clock/` y no validan el texto del editor.

## Ejemplos incluidos

**Simulación → Ejemplo: semáforo y divisores** abre un proyecto con varios módulos y el testbench `tb_clock`; su resultado esperado es `PASS: 72`. **Ejemplo: sumador de 1 bit** abre `full_adder` y `tb_full_adder`; su resultado esperado es `PASS: 8`. Ambos generan un VCD al simularlos con F5.

## Reloj y semáforo

El reloj de referencia inicial es 50 MHz. Puedes cambiar la frecuencia, los periodos de pulso/onda cuadrada, el módulo del contador y las duraciones. Un cambio detiene y reinicia el modelo. Usa Iniciar, Detener, Reiniciar, +1 ciclo, +1 segundo y el selector de aceleración.

Los indicadores se muestrean al refrescar la pantalla. Un pulso de un ciclo a 50 MHz puede no coincidir con ese instante; usa +1 ciclo o el VCD para inspeccionarlo. El motor calcula saltos por eventos y no recorre 50 millones de iteraciones por segundo.

**Crear proyecto HDL** incorpora los parámetros de los controles como valores predeterminados del diseño. El testbench asociado mantiene una configuración de comprobación reducida fija (reloj 4, rojo 3, verde 2, amarillo 1; contador módulo 5) para probar fronteras rápidamente. Cambiar los valores predeterminados no modifica automáticamente ese testbench de regresión.

**Traza de prueba reducida** usa 4 ciclos por segundo virtual, pulso cada 4 y semiperiodo 2; conserva las duraciones de las luces. Registra como máximo 4096 ciclos. Es una visualización didáctica, no una captura física de 50 MHz.

## FPGA y pines

Selecciona un perfil y pulsa **Usar perfil seleccionado**. Los perfiles generales requieren elegir un chip concreto antes de cualquier futura implementación física. Los colores diferencian perfil informativo, simulación lógica compatible y síntesis/programación sin verificar.

Las asignaciones de pines son pares de texto puerto–pin. Pulsa **Aplicar pines** y guarda el proyecto. No se comprueban voltajes, bancos, encapsulados ni conflictos eléctricos; no se genera un bitstream con ellas. Para la placa EP2C5 necesitas su esquema real antes de conectarla.

## Plugins, exportación y diagnóstico

En Plugins, selecciona la carpeta que contiene subcarpetas con `plugin.json`. Descubrir no ejecuta código. Para cargar uno debes aceptar que es código de terceros con acceso a tus archivos. El ejemplo está en `examples/plugins/module_inventory`; selecciona `examples/plugins`, cárgalo y usa **Ejecutar herramienta HDL**.

**Exportar paquete completo** crea una carpeta nueva con `src`, `results`, `manifest.json`, `ports.json` y `project.pforge`. No combina archivos con una carpeta existente. Los puertos que no se pueden analizar se marcan `requires_elaboration`, sin inventar anchos.

Los ajustes y registros se guardan en `%LOCALAPPDATA%\PhoenixForge` en Windows y en el directorio XDG de datos del usuario en Linux. Cada ejecución tiene un directorio independiente. La aplicación no borra automáticamente ese historial; puedes retirarlo cuando hayas guardado tus proyectos. El registro principal rota en tres copias de 2 MiB. Para actualizar, conserva los `.pforge` y la carpeta de datos, y extrae la versión nueva en otra carpeta.


## Componentes y actualizaciones

**Ayuda → Exportar licencias y fuentes de componentes** crea `PhoenixForge_components` dentro de la carpeta elegida, sin sobrescribir una carpeta existente. Permite acceder a los avisos y fuentes incluidos incluso cuando el programa está empaquetado en un solo archivo. En el ZIP de desarrollo solo se exportan los componentes ya presentes.

Los proyectos se ofrecen por defecto en `%LOCALAPPDATA%\PhoenixForge\projects`, aunque puedes elegir cualquier carpeta con permisos. El portable conserva datos en el perfil, no al lado del EXE: cambiar de ordenador requiere copiar los `.pforge` y, si deseas, los ajustes. Al actualizar, cierra la aplicación y reemplaza el ejecutable; no borres la carpeta de datos.

Si el motor incluido no aparece, revisa que ambas rutas personalizadas estén vacías. Si el problema continúa, conserva `PhoenixForge.log` y el informe de la distribución. Digital y GTKWave son integraciones externas opcionales; no se necesitan para el editor, semáforo o visor VCD integrado.
