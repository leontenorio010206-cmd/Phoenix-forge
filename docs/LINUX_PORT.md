# PhœnixForge para Linux · vista previa x86_64

La versión **Windows v1.7.0** continúa siendo la primera estable.
**Linux es un port de vista previa** hasta superar pruebas en computadoras
reales y distintas distribuciones.

## Uso de la carpeta portátil

En Ubuntu 22.04+ / derivados y otras distribuciones compatibles x86_64:

\`\`\`sh
sudo apt-get install iverilog libegl1 libgl1 libxkbcommon-x11-0
tar -xzf PhoenixForge_Linux_x86_64_v1.7.0-preview.tar.gz
cd PhoenixForge-Linux-x86_64
./run-phoenixforge.sh
\`\`\`

- El instalador usa Qt/PySide6 y Python incluidos en la carpeta del
  paquete. No exige pip ni modificar el Python del sistema.
- **Icarus (iverilog/vvp) es una dependencia externa del sistema**:
  se instala con el gestor de paquetes Linux, no se incluye dentro del tar.
- \`./run-phoenixforge.sh --doctor\` inspecciona el entorno.
- \`./run-phoenixforge.sh --self-test /tmp/pf-acceptance --offscreen\`
  ejecuta aceptación gráfica virtual y Verilog real, sin requerir escritorio.
- La aplicación guarda sus datos en \`~/.local/share/PhoenixForge\` o
  \`$XDG_DATA_HOME/PhoenixForge\`.
- La detección USB/Arduino/FPGA es dependiente de herramientas, drivers,
  permisos de usuario, udev y el modelo; **no** está certificada en Linux.
- El puente a Digital requiere Java y Digital seleccionados por el usuario.
- Hay posibilidad de incompatibilidad con Linux anterior a Ubuntu 22.04
  o arquitecturas ARM. No es un AppImage ni un instalador .deb.

## Desarrollo desde fuentes

\`\`\`sh
sudo apt-get install python3-venv iverilog libegl1 libgl1
./install_linux.sh
PF_PYTHON=.venv/bin/python ./run.sh
\`\`\`

## Calidad y distribución

El pipeline de GitHub Actions en Ubuntu 22.04 exige pruebas fuente, HDL
real, aceptación de UI empaquetada en el backend offscreen, y suma
SHA-256 del tar. Si algo falla no sube el paquete como aprobado.

Este paquete previo no está firmado ni validado en un escritorio real.
Licencias de código MIT/Qt LGPL y avisos: \`LICENSE\`,
\`THIRD_PARTY_NOTICES.md\`, \`LEGAL.md\`. Las DLL de Windows no se
distribuyen en Linux. No se debe borrar ninguna obligación de licencia
al reducir el tamaño del paquete.
