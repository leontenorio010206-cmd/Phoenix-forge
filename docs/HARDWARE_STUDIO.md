# Hardware Studio — PhœnixForge 1.6

## Alcance de la primera integración

La detección de conexiones funciona en **Windows**, usando WMI/CIM de Windows por
PowerShell. La pantalla Hardware Studio escanea las interfaces USB y puertos COM
cada 8 segundos mientras está visible. No interfiere con las aplicaciones
instaladas ni instala controladores sin consentimiento.

**Identificación incierta:** VID/PID de un adaptador CH340/FTDI/CP210x no basta
para determinar si corresponde a un Arduino, una FPGA u otro dispositivo. En
esos casos el programa muestra «USB / serie» y solicita elegir placa y puerto.

### Arduino

1. Conecta el Arduino con un cable de datos y entra a **Hardware Studio**.
2. Pulsa **Preparar CLI**: descargará Arduino CLI **v1.5.1 Windows x64** desde la
   distribución oficial con SHA-256 fijado. No afecta el PATH global.
3. Selecciona **Instalar plataforma** para preparar un core oficial `arduino:*`
   (por ejemplo `arduino:avr`). Requiere conexión a Internet y consentimiento.
4. Edita un sketch `.ino` en el editor integrado o abre uno de tu equipo.
5. Elige el **FQBN exacto** y el puerto COM correcto. Pulsa **Compilar sketch**.
6. Para grabar la placa pulsa **Subir al Arduino** y confirma la advertencia.

La compilación conserva los archivos de salida para la carga física.
Arduino CLI y los paquetes de terceros ejecutan código nativo: utiliza
exclusivamente herramientas y bibliotecas de confianza.

### Raspberry Pi Pico

Conecta la Pico en modo **BOOTSEL**. Se detecta un volumen USB `RPI-RP2`.
Pulsa **Subir firmware .uf2** y elige un archivo UF2 válido para tu modelo.
La copia requiere confirmación e inspecciona la cabecera de UF2 y la presencia
de `INFO_UF2.TXT`. **No formatea ni escribe tarjetas SD**.

Una Raspberry Pi 4/5 es un ordenador Linux; la programación Python/C++ se
desarrolla por consola o SSH. Conectar una Pi por USB no implica que esté
configurada como USB gadget. En esta versión ofrecemos documentación y el
modelo de detección, no instalamos SSH en equipos remotos ni modificamos redes.

### FPGA

El catálogo actual conserva los diez perfiles de **simulación RTL** con Icarus.
La detección de adaptadores JTAG como USB-Blaster **no identifica por sí sola**
el dispositivo físico. Para cargar un bitstream son necesarios la placa, el
encapsulado, el cable, los pines de programación y una herramienta compatible.
Se enlazan nextpnr y openFPGALoader para futuras integraciones verificadas.
No se realiza ninguna grabación JTAG en v1.6.

### Controladores y librerías

«Todas las librerías» no es un paquete realista: hay miles de versiones y
dependencias. Se utiliza el gestor oficial Arduino CLI para instalar bajo
petición las bibliotecas que necesite un proyecto.

La detección es automática, **las descargas no**. No se instalan drivers
genéricos basándose en VID/PID: algunos requieren permisos de administrador
y herramientas específicas del fabricante. Esto evita romper el USB, sustituir
drivers JTAG o instalar software de una fuente incorrecta.

### Enlaces de documentación
- https://docs.arduino.cc/arduino-cli/getting-started/
- https://github.com/arduino/arduino-cli/releases/tag/v1.5.1
- https://www.raspberrypi.com/documentation/microcontrollers/
- https://github.com/YosysHQ/nextpnr
- https://github.com/trabucayre/openFPGALoader

### Soporte del ejecutable

La aplicación principal se empaqueta para Windows 10 de 64 bits. El soporte
legacy Windows 7 no está certificado para las herramientas nuevas.
