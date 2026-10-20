# Contribuir a PhœnixForge

1. Crea una rama de trabajo (`feature/nombre` o `fix/nombre`).
2. Añade pruebas para cualquier cambio del motor HDL, perfiles o formato `.pforge`.
3. Ejecuta `python -m pytest -q`. Verifica si hay pruebas omitidas por dependencias ausentes.
4. No subas binarios compilados, entornos virtuales, contraseñas ni archivos `.pforge` con datos personales.
5. Envía los cambios mediante una solicitud de incorporación (pull request), documentando pruebas y capturas reales.
6. El formato `.pforge` es versionado: no lo modifiques sin considerar compatibilidad y migraciones.

Para plugins consulta `docs/PLUGIN_SDK.md`. Los plugins ejecutan código de terceros; usa solamente extensiones de confianza.
