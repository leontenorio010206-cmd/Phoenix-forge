# PhœnixForge 1.6.1 — Arduino: modelos, originales/compatibles y bibliotecas

## Modelos Arduino
Hardware Studio → **Modelos y librerías** incluye accesos iniciales a Uno, Nano,
Mega, Leonardo, Micro, MKR, Nano 33, Nano ESP32, Nano Every, Uno R4,
GIGA, Portenta y otros perfiles. La **lista completa dinámica** la consulta
`arduino-cli board listall --json` desde los *cores ya instalados*.
Al instalar nuevas plataformas de Arduino, sus modelos se incorporan a la lista
al pulsar «Leer catálogo Arduino CLI». Los accesos iniciales pueden necesitar
la descarga de un core antes de compilar.

No afirmamos incluir *literalmente todos* los Arduinos del mercado o
clones de fabricantes externos: Arduino CLI puede ampliar perfiles mediante
el gestor de placas según lo que instales; cada familia usa su FQBN.

## Arduino original vs. clon ("piraña")
La pantalla de detección USB ahora muestra «Origen Arduino»:
- **Identificadores USB Arduino (autenticidad no verificable)** para VID oficiales conocidos.
- **Compatible/clon posible (CH340; no certificado)** cuando el descriptor
  menciona Arduino y usa un puente USB-serie CH340/CH341.
- **No verificable** para adaptadores o dispositivos genéricos.

La identidad USB se puede reproducir/clonar; esto NO prueba si la placa es
original ni garantiza que soporte un bootloader concreto. Puedes identificar
la placa por serigrafía, microcontrolador, esquema y proveedor.

## Bibliotecas
- **Incluidos en la app**: ejemplos fuente propios para Blink, Serial, GPIO,
  PWM, Wire/I2C, SPI, EEPROM y Servo. Funcionan cuando tu placa y sus paquetes
  lo permiten. No contienen código de bibliotecas de terceros.
- **Proporcionados por instalar un core**: `Arduino.h`, `Wire.h`, `SPI.h`,
  `EEPROM.h`, `SoftwareSerial.h` según la plataforma.
- **Paquete adicional**: ArduinoJson, Servo, Adafruit NeoPixel, DHT sensor
  library, Adafruit Unified Sensor, OneWire, DallasTemperature, AccelStepper y
  PubSubClient, desde el índice oficial de Arduino Library Manager.
- **Instalar paquete básico** solicita autorización una sola vez, actualiza
  el índice y luego instala cada biblioteca. Si alguna falla, el resultado
  muestra exactamente cuál y por qué; no se ocultan errores.
- **Ver instaladas** consulta el inventario actual, incluidas las bibliotecas
  de las plataformas.
- **Buscar en línea** consulta bibliotecas actuales desde el gestor Arduino CLI.
- **Actualizar bibliotecas** solicita aprobación y usa Arduino CLI para
  descargar e instalar nuevas versiones de las bibliotecas instaladas.
  Las actualizaciones pueden afectar compatibilidad: conserva tus proyectos.

La descarga/instalación se hace tras autorización, no por conectar USB ni
en segundo plano. Una «biblioteca universal de Arduino» no existe; algunas
bibliotecas solo funcionan en una familia y el usuario debe comprobar soporte.

## Fuentes
- https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_board_listall
- https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_lib_list
- https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_lib_upgrade
- https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_lib_install

## Seguridad
PhœnixForge no instala controladores de Arduino/clones solo con VID/PID;
la interfaz no escribe firmware sin confirmación. Herramientas del gestor
oficial y bibliotecas descargadas pueden ejecutar código externo.
No se ofrecen garantías de autenticidad por USB.
