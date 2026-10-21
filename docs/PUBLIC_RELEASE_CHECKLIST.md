# Lista de verificación antes de abrir PhœnixForge al público

> **Bloqueo de seguridad:** este repositorio privado ha contenido el archivo binario `PhoenixForge_GitHub.git.bundle` en la raíz, una copia de historial Git de ~3 MB. **Antes de cambiar a público** es indispensable verificar que tanto el archivo como los objetos/commits que contiene no expongan credenciales, datos personales ni archivos de otras personas. Borrarlo del árbol actual **no borra el historial** ni los commits de las ramas existentes.

## Trabajo ya preparado

- [x] Licencia MIT del código propio y copyright identificados.
- [x] Cocreador y mantenedor acreditado: Leonardo Antonio Hernández Tenorio.
- [x] Atribución explícita a Digital de Helmut Neemann, bajo GPLv3, y declaración de independencia.
- [x] Avisos de terceros actualizados; Digital y Java se descargan opcionalmente de fuentes oficiales con SHA-256.
- [x] Compilación real de Windows 1.7 aprobada en CI y artefactos con comprobaciones, sin prometer compatibilidad universal.
- [x] Remover la copia `.git.bundle` **del árbol de trabajo de la rama de publicación** (esto no limpia commits históricos).

## Pendiente ANTES de cambiar la visibilidad

- [ ] Auditar **todos los commits, ramas, etiquetas y objetos alcanzables**, incluyendo binarios e historial archivado (por ejemplo, con un escáner de secretos y revisión manual).
- [ ] Si aparecen credenciales o archivos privados, **revocarlos/rotarlos** y limpiar de forma segura el historial con apoyo de GitHub; valorar crear un repositorio público nuevo desde un árbol limpio sin historial privado.
- [ ] Verificar si hay información sensible en proyectos `.pforge`, metadatos de commits, comentarios, capturas, registros y binarios. Obtener permiso de terceros para cualquier material no propio.
- [ ] Revisar obligaciones de redistribución de bibliotecas GPL/LGPL, código fuente correspondiente y avisos en los artefactos finales, incluida la posibilidad de reemplazo de bibliotecas LGPL.
- [ ] Probar al menos en una laptop física Windows 10/11 x64 (arranque, instalación, desinstalación, permisos, Digital opcional, antivirus y uso de memoria).
- [ ] Comprobar que `main` incluye los cambios de la v1.7 y que una compilación de `main` pasa antes de etiquetar.
- [ ] El propietario debe cambiar GitHub **Settings → General → Danger Zone → Change repository visibility → Public** (la integración del asistente no dispone de una acción para cambiar visibilidad).
- [ ] Publicar una edición en **Releases** etiquetada `v1.7.0`, título *PhœnixForge 1.7.0 — Primera estable para Windows x64*, con notas y archivos Setup, Portable, `SHA256SUMS.txt` y fuentes/licencias. La integración actual no tiene acción para crear Releases.
- [ ] Revisar las políticas de permisos de GitHub Actions para repositorio público, y que ninguna ejecución copie secretos a artefactos.

## Distinción importante

*Primera estable* significa **primera versión que aprobó las pruebas automatizadas que hemos definido**; no implica certificación oficial ni ausencia total de errores. La licencia MIT tampoco garantiza automáticamente el cumplimiento de licencias de todo software de terceros.

Consulta [LEGAL.md](../LEGAL.md), [CREDITS.md](../CREDITS.md) y [notas v1.7](RELEASE_1.7.0.md).
