package org.phoenixforge.mobile;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

/**
 * Safe and portable subset of desktop Project (.pforge), schema version 1.
 * Keeps ALL declared HDL and binary artifacts when editing a source.
 * Does not execute imported HDL, ZIP entries, plugins or JavaScript.
 */
public final class PforgeProject {
    static final int MAX_FILES = 512;
    static final long MAX_BYTES = 32L * 1024 * 1024;
    static final int MAX_MANIFEST = 1024 * 1024;

    private final JSONObject manifest;
    private final LinkedHashMap<String, byte[]> payload;

    private PforgeProject(JSONObject manifest, LinkedHashMap<String, byte[]> payload) {
        this.manifest = manifest;
        this.payload = payload;
    }

    public static PforgeProject createDemo() {
        try {
            JSONObject m = new JSONObject();
            m.put("format", "PhoenixForge");
            m.put("schema_version", 1);
            m.put("app_version", "1.7.0");
            m.put("project_id", UUID.randomUUID().toString());
            m.put("name", "Proyecto Android");
            m.put("device", "ep2c5t144c8n");
            m.put("simulation", new JSONObject().put("top", "main").put("testbench", "").put("timeout", 15));
            m.put("pins", new JSONObject());
            m.put("metadata", new JSONObject().put("android_edited", true));
            m.put("export_state", new JSONObject());
            m.put("hdl_files", new JSONArray());
            m.put("artifacts", new JSONArray());
            PforgeProject p = new PforgeProject(m, new LinkedHashMap<>());
            p.addSource("main.v", "module main(input a, input b, output y);\n  assign y = a & b;\nendmodule\n");
            return p;
        } catch (JSONException error) {
            throw new IllegalStateException(error);
        }
    }

    public static PforgeProject read(InputStream input) throws IOException {
        if (input == null) throw new IOException("No se recibió archivo de proyecto");
        LinkedHashMap<String, byte[]> zip = new LinkedHashMap<>();
        Set<String> normalized = new HashSet<>();
        long total = 0L;
        try (ZipInputStream archive = new ZipInputStream(input)) {
            ZipEntry entry;
            while ((entry = archive.getNextEntry()) != null) {
                String path = entry.getName();
                checkPath(path);
                if (entry.isDirectory() || !normalized.add(path.toLowerCase(Locale.ROOT))) {
                    throw new IOException("Entrada ZIP duplicada o directorio: " + path);
                }
                if (zip.size() >= MAX_FILES + 1) throw new IOException("El proyecto contiene demasiados archivos");
                ByteArrayOutputStream buffer = new ByteArrayOutputStream();
                byte[] block = new byte[8192];
                int amount;
                long limit = "manifest.json".equals(path) ? MAX_MANIFEST : MAX_BYTES;
                while ((amount = archive.read(block)) != -1) {
                    total += amount;
                    if (total > MAX_BYTES + MAX_MANIFEST || buffer.size() + (long) amount > limit) {
                        throw new IOException("Proyecto demasiado grande (límite 32 MiB)");
                    }
                    buffer.write(block, 0, amount);
                }
                zip.put(path, buffer.toByteArray());
                archive.closeEntry();
            }
        } catch (SecurityException error) {
            throw new IOException("No se permite acceder al proyecto", error);
        }
        byte[] raw = zip.remove("manifest.json");
        if (raw == null) throw new IOException("Falta manifest.json");
        final JSONObject m;
        try {
            m = new JSONObject(decode(raw));
        } catch (JSONException error) {
            throw new IOException("Manifiesto JSON inválido", error);
        }
        PforgeProject project = new PforgeProject(m, zip);
        project.validate();
        return project;
    }

    public String getName() {
        return manifest.optString("name", "Proyecto");
    }

    public List<String> files() {
        ArrayList<String> names = new ArrayList<>();
        JSONArray listing = manifest.optJSONArray("hdl_files");
        if (listing != null) {
            for (int i = 0; i < listing.length(); i++) {
                JSONObject item = listing.optJSONObject(i);
                if (item != null) names.add(item.optString("path", "").substring(4));
            }
        }
        return names;
    }

    public String getSource(String name) throws IOException {
        byte[] data = payload.get("src/" + name);
        if (data == null) throw new IOException("Archivo HDL no encontrado: " + name);
        return decode(data);
    }

    public void addSource(String name, String content) throws IOException {
        checkPath(name);
        if (!name.toLowerCase(Locale.ROOT).endsWith(".v")
                && !name.toLowerCase(Locale.ROOT).endsWith(".sv")) {
            throw new IOException("Solo se admiten fuentes .v y .sv para crear");
        }
        String path = "src/" + name;
        for (String other : payload.keySet()) {
            if (other.equalsIgnoreCase(path)) throw new IOException("Ya existe este nombre de archivo");
        }
        if (payload.size() >= MAX_FILES) throw new IOException("Límite de archivos alcanzado");
        byte[] bytes = content.getBytes(StandardCharsets.UTF_8);
        if (bytes.length > MAX_BYTES) throw new IOException("Archivo demasiado grande");
        try {
            manifest.getJSONArray("hdl_files").put(
                    new JSONObject().put("path", path).put("sha256", sha256(bytes)));
        } catch (JSONException error) {
            throw new IOException("No se puede registrar el archivo", error);
        }
        payload.put(path, bytes);
        checkTotalSize();
    }

    public void setSource(String name, String content) throws IOException {
        String path = "src/" + name;
        if (!payload.containsKey(path)) throw new IOException("El archivo no existe: " + name);
        byte[] bytes = content.getBytes(StandardCharsets.UTF_8);
        byte[] old = payload.put(path, bytes);
        try {
            checkTotalSize();
            JSONArray hdl = manifest.getJSONArray("hdl_files");
            for (int i = 0; i < hdl.length(); i++) {
                JSONObject item = hdl.getJSONObject(i);
                if (path.equals(item.getString("path"))) {
                    item.put("sha256", sha256(bytes));
                    return;
                }
            }
            throw new IOException("Archivo no declarado en el manifiesto");
        } catch (IOException | JSONException error) {
            payload.put(path, old);
            throw new IOException("No se pudo actualizar HDL: " + error.getMessage(), error);
        }
    }

    public void save(OutputStream output) throws IOException {
        validate();
        // Re-export the complete content, preserving project_id, metadata and artifacts.
        try {
            manifest.put("app_version", "1.7.0");
            byte[] raw = manifest.toString(2).getBytes(StandardCharsets.UTF_8);
            if (raw.length > MAX_MANIFEST) throw new IOException("Manifiesto demasiado grande");
            try (ZipOutputStream archive = new ZipOutputStream(output)) {
                writeEntry(archive, "manifest.json", raw);
                for (Map.Entry<String, byte[]> entry : payload.entrySet()) {
                    writeEntry(archive, entry.getKey(), entry.getValue());
                }
                archive.finish();
            }
        } catch (JSONException error) {
            throw new IOException("No se pudo guardar el manifiesto", error);
        }
    }

    private static void writeEntry(ZipOutputStream archive, String name, byte[] data) throws IOException {
        ZipEntry entry = new ZipEntry(name);
        archive.putNextEntry(entry);
        archive.write(data);
        archive.closeEntry();
    }

    public void validate() throws IOException {
        try {
            if (!"PhoenixForge".equals(manifest.getString("format"))
                    || manifest.getInt("schema_version") != 1) {
                throw new IOException("Formato .pforge no compatible con versión 1");
            }
            UUID.fromString(manifest.getString("project_id"));
            String name = manifest.getString("name");
            if (name.trim().isEmpty() || name.length() > 200) throw new IOException("Nombre de proyecto inválido");
            if (manifest.getString("device").isEmpty()) throw new IOException("Dispositivo sin identificar");
            manifest.getJSONObject("simulation");
            manifest.getJSONObject("pins");
            manifest.getJSONObject("metadata");
            manifest.getJSONObject("export_state");
            JSONArray hdl = manifest.getJSONArray("hdl_files");
            JSONArray artifacts = manifest.getJSONArray("artifacts");
            if (hdl.length() + artifacts.length() != payload.size() || payload.size() > MAX_FILES) {
                throw new IOException("Entradas del manifiesto diferentes a las del archivo ZIP");
            }
            HashSet<String> seen = new HashSet<>();
            checkArray(hdl, "src/", seen);
            checkArray(artifacts, "results/", seen);
            checkTotalSize();
        } catch (JSONException | IllegalArgumentException error) {
            throw new IOException("Manifiesto de proyecto incorrecto", error);
        }
    }

    private void checkArray(JSONArray list, String prefix, Set<String> seen)
            throws JSONException, IOException {
        for (int i = 0; i < list.length(); i++) {
            JSONObject item = list.getJSONObject(i);
            String path = item.getString("path");
            checkPath(path);
            if (!path.startsWith(prefix) || path.length() <= prefix.length()
                    || !seen.add(path.toLowerCase(Locale.ROOT))) {
                throw new IOException("Entrada duplicada, fuera de grupo o insegura: " + path);
            }
            byte[] bytes = payload.get(path);
            if (bytes == null || !sha256(bytes).equalsIgnoreCase(item.getString("sha256"))) {
                throw new IOException("Integridad incorrecta de " + path);
            }
            if ("src/".equals(prefix)) decode(bytes); // UTF-8 must be valid like on desktop.
        }
    }

    private void checkTotalSize() throws IOException {
        long total = 0;
        for (byte[] data : payload.values()) {
            total += data.length;
            if (total > MAX_BYTES) throw new IOException("Proyecto supera 32 MiB");
        }
    }

    private static String sha256(byte[] bytes) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            StringBuilder result = new StringBuilder();
            for (byte b : md.digest(bytes)) result.append(String.format(Locale.ROOT, "%02x", b & 0xff));
            return result.toString();
        } catch (NoSuchAlgorithmException error) {
            throw new AssertionError(error);
        }
    }

    private static String decode(byte[] bytes) throws IOException {
        try {
            return StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes)).toString();
        } catch (CharacterCodingException error) {
            throw new IOException("El archivo HDL/manifest no contiene UTF-8 válido", error);
        }
    }

    static void checkPath(String path) throws IOException {
        if (path == null || path.isEmpty() || path.length() > 220
                || path.startsWith("/") || path.indexOf('\\') >= 0) {
            throw new IOException("Ruta ZIP insegura");
        }
        String invalid = ":*?\"<>|";
        for (int i = 0; i < path.length(); i++) {
            char c = path.charAt(i);
            if (c < 32 || invalid.indexOf(c) >= 0) throw new IOException("Caracteres de ruta inválidos");
        }
        for (String part : path.split("/", -1)) {
            if (part.isEmpty() || part.equals(".") || part.equals("..")
                    || part.endsWith(".") || part.endsWith(" ")) {
                throw new IOException("Ruta relativa insegura");
            }
            String base = part.split("\\.", 2)[0].toUpperCase(Locale.ROOT);
            if (base.equals("CON") || base.equals("PRN") || base.equals("AUX") || base.equals("NUL")
                    || base.matches("COM[1-9]") || base.matches("LPT[1-9]")) {
                throw new IOException("Nombre reservado en Windows");
            }
        }
    }
}
