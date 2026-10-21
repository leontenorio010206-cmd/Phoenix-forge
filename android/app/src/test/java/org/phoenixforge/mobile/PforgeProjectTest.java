package org.phoenixforge.mobile;

import org.junit.Test;
import static org.junit.Assert.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

public final class PforgeProjectTest {
    private static byte[] bytes(String text) {
        return text.getBytes(StandardCharsets.UTF_8);
    }

    private static String hex(byte[] bytes) throws Exception {
        StringBuilder result = new StringBuilder();
        for (byte b : MessageDigest.getInstance("SHA-256").digest(bytes)) {
            result.append(String.format(java.util.Locale.ROOT, "%02x", b & 0xff));
        }
        return result.toString();
    }

    private static byte[] zip(Map<String, byte[]> entries) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        try (ZipOutputStream archive = new ZipOutputStream(output)) {
            for (Map.Entry<String, byte[]> e : entries.entrySet()) {
                archive.putNextEntry(new ZipEntry(e.getKey()));
                archive.write(e.getValue());
                archive.closeEntry();
            }
        }
        return output.toByteArray();
    }

    @Test
    public void demoIsValidAndDesktopRoundtripRetainsModifiedCode() throws Exception {
        PforgeProject p = PforgeProject.createDemo();
        p.setSource("main.v", "module main(input x,output y);assign y=x;endmodule\n");
        p.addSource("other.sv", "module other;endmodule\n");
        ByteArrayOutputStream saved = new ByteArrayOutputStream();
        p.save(saved);
        PforgeProject loaded = PforgeProject.read(new ByteArrayInputStream(saved.toByteArray()));
        assertEquals(p.files(), loaded.files());
        assertEquals(p.getSource("main.v"), loaded.getSource("main.v"));
        assertTrue(loaded.getSource("other.sv").contains("endmodule"));
    }

    @Test
    public void preservesDesktopMetadataProjectIdPinsAndArtifactBytes() throws Exception {
        String id = UUID.randomUUID().toString();
        byte[] verilog = bytes("module tb; initial $finish; endmodule\n");
        byte[] vcd = bytes("$date now $end\n#0\n0!\n");
        JSONObject m = new JSONObject()
            .put("format","PhoenixForge")
            .put("schema_version",1)
            .put("app_version","1.7.0")
            .put("project_id",id)
            .put("name","Proyecto desde PC")
            .put("device","gw1n")
            .put("simulation",new JSONObject().put("top","tb").put("testbench","tb").put("timeout",15))
            .put("pins",new JSONObject().put("led","P21"))
            .put("metadata",new JSONObject().put("my_notes","conservar íntegro"))
            .put("export_state",new JSONObject().put("format","keep"))
            .put("hdl_files",new JSONArray().put(
                new JSONObject().put("path","src/tb.v").put("sha256",hex(verilog))))
            .put("artifacts",new JSONArray().put(
                new JSONObject().put("path","results/trace.vcd").put("sha256",hex(vcd))));
        Map<String,byte[]> data = new java.util.LinkedHashMap<>();
        data.put("manifest.json",bytes(m.toString()));
        data.put("src/tb.v",verilog);
        data.put("results/trace.vcd",vcd);
        PforgeProject project = PforgeProject.read(new ByteArrayInputStream(zip(data)));
        project.setSource("tb.v", "module tb; initial #5 $finish; endmodule\n");
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        project.save(out);
        Map<String,byte[]> reread = new HashMap<>();
        try (ZipInputStream archive = new ZipInputStream(new ByteArrayInputStream(out.toByteArray()))) {
            ZipEntry e;
            while ((e = archive.getNextEntry()) != null) {
                ByteArrayOutputStream b = new ByteArrayOutputStream();
                byte[] chunk = new byte[256];
                int n;
                while ((n = archive.read(chunk)) != -1) b.write(chunk,0,n);
                reread.put(e.getName(),b.toByteArray());
            }
        }
        JSONObject updated = new JSONObject(new String(reread.get("manifest.json"),StandardCharsets.UTF_8));
        assertEquals(id,updated.getString("project_id"));
        assertEquals("P21",updated.getJSONObject("pins").getString("led"));
        assertEquals("conservar íntegro",updated.getJSONObject("metadata").getString("my_notes"));
        assertEquals("keep",updated.getJSONObject("export_state").getString("format"));
        assertArrayEquals(vcd,reread.get("results/trace.vcd"));
        assertEquals(hex(reread.get("src/tb.v")),
                     updated.getJSONArray("hdl_files").getJSONObject(0).getString("sha256"));
    }

    @Test
    public void refusesZipPathTraversalAndWrongDigest() throws Exception {
        Map<String,byte[]> bad = new java.util.LinkedHashMap<>();
        bad.put("../escape.txt",bytes("danger"));
        try {
            PforgeProject.read(new ByteArrayInputStream(zip(bad)));
            fail("Path traversal must not be accepted");
        } catch (java.io.IOException expected) {
            assertTrue(expected.getMessage().contains("Ruta"));
        }
        PforgeProject demo = PforgeProject.createDemo();
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        demo.save(out);
        Map<String,byte[]> tampered = new java.util.LinkedHashMap<>();
        try (ZipInputStream archive = new ZipInputStream(new ByteArrayInputStream(out.toByteArray()))) {
            ZipEntry e;
            while ((e = archive.getNextEntry()) != null) {
                ByteArrayOutputStream b = new ByteArrayOutputStream();
                byte[] chunk = new byte[256];
                int n;
                while ((n = archive.read(chunk)) != -1) b.write(chunk,0,n);
                tampered.put(e.getName(),b.toByteArray());
            }
        }
        tampered.put("src/main.v",bytes("module hacked;endmodule"));
        try {
            PforgeProject.read(new ByteArrayInputStream(zip(tampered)));
            fail("Digest modification must not pass");
        } catch (java.io.IOException expected) {
            assertTrue(expected.getMessage().contains("Integridad"));
        }
    }

    @Test
    public void rejectsDuplicateNamesAndWindowsReservedPaths() throws Exception {
        for (String bad : new String[] {"../evil.v","/etc/passwd","a\\b.v","CON.v","a//b.v","a/./b.v","a/../b.v"}) {
            try {
                PforgeProject.checkPath(bad);
                fail("Unsafe path allowed: "+bad);
            } catch (java.io.IOException expected) { }
        }
        PforgeProject p = PforgeProject.createDemo();
        try {
            p.addSource("MAIN.V", "module other;endmodule");
            fail("Windows-insensitive duplicate allowed");
        } catch (java.io.IOException expected) { }
    }
}
