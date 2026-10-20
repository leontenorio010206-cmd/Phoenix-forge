# Referencias académicas y decisiones de diseño

## Práctica 6.0 · reloj, contador y semáforo

La práctica proporciona una referencia de placa de 50 MHz, el ejemplo de 104.16 microsegundos y el ejercicio del semáforo. Los cálculos utilizados son:

- Periodo de reloj: `1 / 50,000,000 s = 20 ns`.
- `104.16 µs / 20 ns = 5,208` ciclos.
- `ceil(log2(5,208)) = 13` bits; un contador módulo 5,208 recorre 0…5,207.
- `ceil(log2(50,000,000)) = 26` bits; un contador de un segundo recorre 0…49,999,999.

Se corrigen los anchos insuficientes indicados en el material. La conversión correcta es `1 s = 1,000,000,000 ns`. El reloj de 50 MHz es la referencia de esa placa y no una frecuencia máxima atribuida al chip.

| Función | Parámetro a 50 MHz | Resultado |
|---|---:|---|
| Pulso periódico | `CYCLES=50,000,000` | Un pulso de 20 ns cada segundo |
| Onda cuadrada de 1 Hz | `HALF_CYCLES=25,000,000` | Cambia de nivel cada 0.5 s; periodo de 1 s |
| Cambio de nivel cada segundo | `HALF_CYCLES=50,000,000` | Onda de 0.5 Hz |

El módulo de pulsos usa un pulso de habilitación de un ciclo. El divisor cuadrado tiene salida separada. El semáforo mantiene un solo dominio de reloj y actualiza su estado con una habilitación; no usa lógica combinacional como reloj derivado.

**Decisiones añadidas por esta implementación:** orden rojo → verde → amarillo; duraciones iniciales 5/5/2 segundos; LED activos altos; reset síncrono activo alto; contador ascendente; sin intermitencia ni detección peatonal. El PDF no fija estas decisiones como una tabla completa de estados.

El laboratorio permite configurar reloj, módulo del contador, periodo del pulso, semiperiodo y duraciones. El generador transmite esos valores a los parámetros HDL. El testbench de regresión usa una instancia reducida de 4 Hz y tiempos 3/2/1 para comprobar 72 ciclos, incluidos límites y tres periodos, sin ejecutar millones de ciclos. Sus parámetros reducidos son explícitos y no representan una medida física de tiempo real.

Las trazas internas usan también un reloj reducido de 4 Hz, con un límite de 4,096 ciclos; sus metadatos identifican el límite. La animación con aceleración usa saltos de eventos enteros, no pretende reproducir señales eléctricas ni medir precisión de un oscilador.

## Tutorial Verilog

Se consultaron las secciones de módulos, puertos, `assign`, `always`, `initial` y testbenches del tutorial suministrado. Los ejemplos usan `$dumpfile`/`$dumpvars` para VCD portable en Icarus, en lugar de las tareas de forma de onda específicas de herramientas comerciales que aparecen en el tutorial. Los retardos se reservan para testbenches. La aceptación de construcciones de inicialización para síntesis depende del dispositivo y de la herramienta; esta versión no certifica síntesis.

Los PDFs académicos originales no se redistribuyen en el ZIP. Se conservan las referencias del laboratorio secuencial.

## Lógica combinacional genérica

El motor Quine–McCluskey permanece independiente en `app/simulators/boolean.py`. Acepta hasta seis variables y términos indiferentes; minimiza cantidad de términos y después literales. No tiene una pantalla específica en esta versión.

El ejemplo `full_adder` es un sumador completo de un bit: entradas a, b, cin; salidas sum y cout. El testbench recorre las ocho combinaciones y compara con suma aritmética. Es un ejemplo propio de regresión, sin atribuir su contenido al PDF.
