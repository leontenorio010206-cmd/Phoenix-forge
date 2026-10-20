# Compatibilidad y aceptación

## Estado comprobado

| Entorno | Estado de 1.1 |
|---|---|
| Linux x64, Python 3.12.14, PySide6/Qt 6.8.3 | Pruebas de código e interfaz offscreen ejecutadas; detalle en VERIFICATION.md |
| Icarus 12.0 / vvp en Linux | Sumador, secuenciales, errores, tiempo máximo y cancelación probados |
| Windows 10 x64, 1809 o posterior | Objetivo obligatorio; no hay EXE construido/verificado todavía |
| Runner `windows-2022` | Workflow preparado; no ejecutado. Es Windows Server 2022, no Windows 10 |
| VM Windows 10 sin Python/Qt/Icarus | Pendiente; necesaria para cerrar la aceptación |
| Windows 7 SP1 x64 | Candidato heredado experimental, sin prueba nativa y sin soporte declarado |

Qt offscreen muestra y renderiza widgets reales sin escritorio nativo; no prueba controladores Windows, DPI ni instalación. Ninguna prueba Linux se atribuye a Windows. Una prueba bajo Wine tampoco se acepta como Windows nativo.

## Versiones y restricciones

El objetivo moderno fija Python 3.11.9 x64, PySide6/Qt 6.8.3, PyInstaller 6.22.3 y hooks 2026.8. Qt 6.8 requiere Windows 10 1809 o posterior; esa es la restricción efectiva. Python 3.11.9 se elige por su instalador binario oficial de la rama, sin presentarlo como el parche más reciente. Los requisitos están en `requirements/`.

El entorno heredado conserva Python 3.8.10 Windows, PySide2 5.15.2.1/Qt 5.15.2 y PyInstaller 4.10. Python 3.8 está fuera de mantenimiento. Win7 necesita actualizaciones como KB2533623; PyInstaller 4.10 no garantiza soporte Win7. La combinación histórica documental no demuestra que este programa funcione allí. No se genera su candidato por el workflow moderno ni se promete Icarus autónomo para él.

Icarus Windows se construye desde v12_0 con MinGW x64 y se recogen sus DLLs importadas. Los tests empaquetados deben probar esos binarios exactos. GTKWave y Digital son externos opcionales y no condicionan la distribución principal.

## Aceptación reproducible en Windows 10 limpio

1. Use VM x64 con Windows 10 22H2 o build admitida; registre edición, build, fecha, cuenta sin administrador, escala DPI y resolución. No instale Python, Qt, Icarus ni herramientas de desarrollo.
2. Copie el portable y verifique SHA-256 contra el informe del artefacto. Desconecte la red para comprobar que no descarga nada al arrancar.
3. Abra con doble clic. Confirme ventana, logo, diez perfiles, manual y los dos ejemplos desde el menú Simulación. Pruebe resoluciones 1000×680 y 1366×768, escalas 100%, 125% y 150%.
4. Edite dos módulos, busque, deshaga y rehaga. Verifique cambios pendientes, Guardar como y confirmación de sobrescritura. Guarde en una ruta con espacios y acentos.
5. Inicie/detenga/acelere/reinicie semáforo; cambie duraciones y compruebe indicadores y parámetros HDL.
6. Con rutas de Icarus vacías, ejecute ambos ejemplos: `PASS: 8` y `PASS: 72`. Deben generar VCD visible. Introduzca error HDL, `$fatal`, `$stop` y un bucle sin fin; deben fallar o cancelarse sin bloquear la UI.
7. Guarde un proyecto con resultados, cierre y abra de nuevo. Abra el proyecto guardado y compruebe fuentes, VCD y perfil. Verifique que `%LOCALAPPDATA%\PhoenixForge` conserva datos al cerrar el portable.
8. Mueva el EXE de carpeta y repita. Pruebe desde una carpeta sin permiso de escritura, con TEMP escribible. Los ajustes y proyectos no deben depender de esa carpeta.
9. En otra instantánea, ejecute Setup, acceso Inicio y escritorio opcional; desinstale y compruebe que proyectos y configuración permanecen. Reinstale y reabra el proyecto.
10. Conserve capturas, logs y hashes. El arnés opcional `EXE --self-test CARPETA --require-bundled` genera evidencia sin necesitar Python; su ejecución es una acción de prueba, no un requisito del usuario final.

El informe distingue arranque nativo, pruebas en runner y VM limpia. Ninguna se marca aprobada hasta ejecutarla sobre el binario real.
