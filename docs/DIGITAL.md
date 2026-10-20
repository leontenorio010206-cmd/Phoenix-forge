# Digital y otros simuladores externos

Digital de Helmut Neemann es opcional y no participa en el arranque ni en la simulación interna de PhœnixForge 1.1.

La exportación genérica produce Verilog, testbench, VCD, `manifest.json`, `ports.json` y `.pforge`. Los metadatos de puertos reconocen declaraciones literales; los casos que necesitan elaboración quedan marcados. Pueden usarse como base para configurar manualmente un componente externo en Digital.

No hay exportador `.dig` genérico operativo en esta versión, ni se fabrica un JAR. El adaptador dedicado al ejercicio retirado ya no forma parte de la distribución. El paso pendiente es traducir y validar los puertos y parámetros del módulo arbitrario al formato `External` de una versión concreta de Digital, resolver su compilador externo y ejecutar pruebas de equivalencia.

Referencia primaria: https://github.com/hneemann/Digital

Tinkercad y Logisim-evolution permanecen como investigación posterior. Ninguna de estas integraciones condiciona el editor, los modelos internos, los proyectos o el visor VCD.
