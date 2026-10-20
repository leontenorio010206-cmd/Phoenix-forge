# Importar PhœnixForge y compilar el EXE

## Solo una subida manual (sin Git en tu PC)

1. Descarga el archivo `PhoenixForge_GitHub.git.bundle` preparado en ChatGPT.
2. Entra a **Add file → Upload files**: https://github.com/leontenorio010206-cmd/Phoenix-forge/upload/main
3. Arrastra `PhoenixForge_GitHub.git.bundle` (3.1 MB) a la ventana.
4. Pulsa **Commit changes** directamente a `main`.
5. El flujo `PhoenixForge | Importar y compilar Windows` se ejecutará automáticamente, en un runner de Windows.
6. Sigue su avance en https://github.com/leontenorio010206-cmd/Phoenix-forge/actions
7. Abre la ejecución más reciente y descarga **PhoenixForge-Windows-v1.1** desde **Artifacts**, si se ha generado.

## Qué hace el workflow

- Recupera el historial y copia todos los archivos de código al repositorio.
- Instala Python 3.11, Qt y herramientas de compilación en el entorno de GitHub Actions.
- Construye Icarus Verilog y prepara sus dependencias.
- Intenta una compilación completa con pruebas.
- Si las pruebas estrictas fallan, intenta generar un EXE **EXPERIMENTAL NO VERIFICADO**.
- Conserva logs y reportes en **PhoenixForge-Diagnosticos**.

**Nota:** un runner Windows Server 2022 no equivale a una prueba en Windows 10 limpio. La versión se considerará estable cuando se compruebe también en ese sistema y su motor HDL funcione correctamente.

El repositorio debe permanecer privado mientras se revisan las licencias y la estabilidad.
