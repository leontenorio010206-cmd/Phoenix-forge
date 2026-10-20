"""Built-in Arduino quickstart catalogue, not copyrighted vendor libraries.

Board inventory can be extended dynamically using official Arduino CLI boards
manager. Core libraries are provided by installed board platforms, not by us.
"""
from dataclasses import dataclass

# Preloaded shortcuts are not an exhaustive Arduino model database. CLI owns that.
BOARD_SHORTCUTS = (
    ("Uno R3", "arduino:avr:uno", "arduino:avr"),
    ("Nano clásico", "arduino:avr:nano", "arduino:avr"),
    ("Nano compatible · bootloader antiguo", "arduino:avr:nano:cpu=atmega328old", "arduino:avr"),
    ("Mega 2560", "arduino:avr:mega", "arduino:avr"),
    ("Leonardo", "arduino:avr:leonardo", "arduino:avr"),
    ("Micro", "arduino:avr:micro", "arduino:avr"),
    ("Pro Mini", "arduino:avr:pro", "arduino:avr"),
    ("Mini", "arduino:avr:mini", "arduino:avr"),
    ("Esplora", "arduino:avr:esplora", "arduino:avr"),
    ("LilyPad", "arduino:avr:lilypad", "arduino:avr"),
    ("Uno WiFi Rev2", "arduino:megaavr:uno2018", "arduino:megaavr"),
    ("Nano Every", "arduino:megaavr:nona4809", "arduino:megaavr"),
    ("MKR Zero", "arduino:samd:mkrzero", "arduino:samd"),
    ("MKR WiFi 1010", "arduino:samd:mkrwifi1010", "arduino:samd"),
    ("MKR WAN 1310", "arduino:samd:mkrwan1310", "arduino:samd"),
    ("MKR GSM 1400", "arduino:samd:mkrgsm1400", "arduino:samd"),
    ("Nano 33 IoT", "arduino:samd:nano_33_iot", "arduino:samd"),
    ("Nano 33 BLE", "arduino:mbed_nano:nano33ble", "arduino:mbed_nano"),
    ("Nano RP2040 Connect", "arduino:mbed_nano:nanorp2040connect", "arduino:mbed_nano"),
    ("Uno R4 Minima", "arduino:renesas_uno:unor4minima", "arduino:renesas_uno"),
    ("Uno R4 WiFi", "arduino:renesas_uno:unor4wifi", "arduino:renesas_uno"),
    ("Nano ESP32", "arduino:esp32:nano_nora", "arduino:esp32"),
    ("GIGA R1 WiFi", "arduino:mbed_giga:giga", "arduino:mbed_giga"),
    ("Portenta H7", "arduino:mbed_portenta:envie_m7", "arduino:mbed_portenta"),
    ("Raspberry Pi Pico (Arduino)", "arduino:mbed_rp2040:pico", "arduino:mbed_rp2040"),
)
DEFAULT_CORES = ("arduino:avr", "arduino:megaavr", "arduino:samd",
                 "arduino:renesas_uno", "arduino:mbed_nano", "arduino:mbed_rp2040")
# Bundled in the platform installation, not separate ZIP archives.
CORE_HEADERS = ("Arduino.h", "Wire.h", "SPI.h", "EEPROM.h", "SoftwareSerial.h")
# Curated third-party libraries installed from the official Library Manager index.
BASIC_PACK = ("ArduinoJson", "Servo", "Adafruit NeoPixel", "DHT sensor library",
              "Adafruit Unified Sensor", "OneWire", "DallasTemperature",
              "AccelStepper", "PubSubClient")
EXAMPLES = {
    "Blink": """// Blink: usa LED_BUILTIN de la placa seleccionada.
void setup() { pinMode(LED_BUILTIN, OUTPUT); }
void loop() {
  digitalWrite(LED_BUILTIN, HIGH); delay(500);
  digitalWrite(LED_BUILTIN, LOW); delay(500);
}
""",
    "Serial": """void setup() { Serial.begin(9600); }
void loop() { Serial.println("PhoenixForge"); delay(1000); }
""",
    "Entradas digitales": """const int boton = 2;
void setup() {
  pinMode(boton, INPUT_PULLUP);
  pinMode(LED_BUILTIN, OUTPUT);
}
void loop() { digitalWrite(LED_BUILTIN, digitalRead(boton) == LOW); }
""",
    "PWM": """const int salida = 9; // Revisa si tu placa admite PWM en este pin.
void setup() { pinMode(salida, OUTPUT); }
void loop() {
  for (int valor=0; valor<=255; valor+=5) {
    analogWrite(salida, valor); delay(15);
  }
}
""",
    "I2C / Wire": """#include <Wire.h>
void setup() { Wire.begin(); }
void loop() { delay(1000); }
""",
    "SPI": """#include <SPI.h>
void setup() { SPI.begin(); }
void loop() { delay(1000); }
""",
    "EEPROM (solo placas compatibles)": """#include <EEPROM.h>
void setup() { EEPROM.update(0, 42); }
void loop() {}
""",
    "Servo (requiere biblioteca)": """#include <Servo.h>
Servo servo;
void setup() { servo.attach(9); }
void loop() {
  servo.write(0); delay(700);
  servo.write(90); delay(700);
}
""",
}


def model_shortcuts():
    return tuple(BOARD_SHORTCUTS)


def merge_catalog(known, discovered):
    """Deduplicate FQBNs from offline shortcuts + installed cores' live inventory."""
    entries = {fqbn: (name, fqbn, core)
               for name, fqbn, core in known}
    for item in discovered:
        if not isinstance(item, dict):
            continue
        fqbn = str(item.get("fqbn", ""))
        name = str(item.get("name", ""))
        parts = fqbn.split(":")
        if len(parts) == 3 and all(parts) and len(fqbn) <= 150:
            entries[fqbn] = (name[:140] or fqbn, fqbn, ":".join(parts[:2]))
    return tuple(sorted(entries.values(), key=lambda x: x[0].casefold()))
