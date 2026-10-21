package org.phoenixforge.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.text.TextWatcher;
import android.text.Editable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * PhœnixForge Mobile alpha: a touch editor and fully compatible .pforge
 * import/export bridge. NO Android HDL simulator or JTAG programmer yet.
 */
public final class MainActivity extends Activity {
    private static final int OPEN_PROJECT = 1001;
    private static final int SAVE_PROJECT = 1002;
    private static final int BG = 0xFF101827;
    private static final int PANEL = 0xFF162238;
    private static final int TEXT = 0xFFEAF2FF;
    private static final int MUTED = 0xFFA6B5CC;
    private static final int ORANGE = 0xFFEC773D;

    private PforgeProject project;
    private EditText code;
    private Spinner filenames;
    private TextView title;
    private TextView status;
    private String selectedFile;
    private boolean changingFile;
    private boolean dirty;

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("PhœnixForge Mobile");
        project = PforgeProject.createDemo();
        createUi();
        refreshFiles("main.v");
        setStatus("Editor móvil alpha. Compatible con proyectos .pforge de Windows/Linux.");
    }

    private void createUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG);
        root.setPadding(dp(12), dp(12), dp(12), dp(10));

        title = new TextView(this);
        title.setTextSize(21f);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setTextColor(TEXT);
        title.setText("🦅 PhœnixForge");
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("ANDROID · ALPHA 0.1 · EDITOR VERILOG");
        subtitle.setTextSize(11f);
        subtitle.setTextColor(ORANGE);
        root.addView(subtitle);

        HorizontalScrollView barScroll = new HorizontalScrollView(this);
        barScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        addButton(bar, "Nuevo", view -> askNewProject());
        addButton(bar, "Abrir .pforge", view -> chooseProject());
        addButton(bar, "Guardar .pforge", view -> saveProject());
        addButton(bar, "Añadir .v", view -> askNewSource());
        addButton(bar, "Resumen HDL", view -> showHdlSummary());
        barScroll.addView(bar);
        root.addView(barScroll);

        filenames = new Spinner(this);
        filenames.setBackgroundColor(0xFFE9EEF6);
        LinearLayout.LayoutParams selectorParams =
                new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(48));
        selectorParams.topMargin = dp(10);
        root.addView(filenames, selectorParams);
        filenames.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                if (changingFile || project == null) return;
                String requested = (String) parent.getItemAtPosition(position);
                if (requested.equals(selectedFile)) return;
                try {
                    syncEditor();
                    selectedFile = requested;
                    changingFile = true;
                    code.setText(project.getSource(requested));
                    code.setSelection(0);
                    changingFile = false;
                    setStatus("Editando " + requested);
                } catch (IOException error) {
                    changingFile = false;
                    showError("Cambio de archivo", error);
                }
            }
            @Override public void onNothingSelected(AdapterView<?> parent) { }
        });

        code = new EditText(this);
        code.setBackgroundColor(PANEL);
        code.setTextColor(TEXT);
        code.setHintTextColor(MUTED);
        code.setHint("// Escribe aquí tu módulo Verilog");
        code.setTextSize(14f);
        code.setTypeface(Typeface.MONOSPACE);
        code.setGravity(Gravity.TOP | Gravity.START);
        code.setPadding(dp(12), dp(12), dp(12), dp(12));
        code.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE |
                InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        code.setHorizontallyScrolling(true);
        code.setHorizontalScrollBarEnabled(true);
        code.setVerticalScrollBarEnabled(true);
        LinearLayout.LayoutParams codeParams =
                new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
        codeParams.topMargin = dp(8);
        root.addView(code, codeParams);
        code.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                if (!changingFile) dirty = true;
            }
            @Override public void afterTextChanged(Editable s) { }
        });

        status = new TextView(this);
        status.setTextSize(12f);
        status.setTextColor(MUTED);
        status.setPadding(0, dp(8), 0, 0);
        root.addView(status);

        TextView limit = new TextView(this);
        limit.setText("No ejecuta simulación FPGA ni controla USB/JTAG en esta alpha.");
        limit.setTextColor(0xFFF6B88F);
        limit.setTextSize(11f);
        root.addView(limit);
        setContentView(root);
    }

    private void addButton(LinearLayout bar, String title, View.OnClickListener click) {
        Button button = new Button(this);
        button.setText(title);
        button.setTextColor(Color.WHITE);
        button.setTextSize(11f);
        button.setAllCaps(false);
        button.setBackgroundTintList(ColorStateList.valueOf(ORANGE));
        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(46));
        params.rightMargin = dp(6);
        bar.addView(button, params);
        button.setOnClickListener(click);
    }

    private int dp(float value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void setStatus(String text) {
        if (status != null) status.setText(text);
    }

    private void showError(String where, Exception error) {
        new AlertDialog.Builder(this)
                .setTitle(where)
                .setMessage(error.getMessage())
                .setPositiveButton("Aceptar", null).show();
    }

    private void syncEditor() throws IOException {
        if (selectedFile != null && code != null && !changingFile) {
            project.setSource(selectedFile, code.getText().toString());
        }
    }

    private void refreshFiles(String preferred) {
        changingFile = true;
        List<String> names = project.files();
        ArrayAdapter<String> adapter = new ArrayAdapter<>(
                this, android.R.layout.simple_spinner_item, names);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        filenames.setAdapter(adapter);
        String target = names.contains(preferred) ? preferred : (names.isEmpty() ? null : names.get(0));
        selectedFile = target;
        if (target != null) {
            code.setText("");
            try {
                code.setText(project.getSource(target));
            } catch (IOException error) {
                showError("HDL", error);
            }
            filenames.setSelection(names.indexOf(target));
            code.setSelection(0);
        } else {
            code.setText("// Este proyecto no contiene código HDL.\n");
            code.setEnabled(false);
        }
        code.setEnabled(target != null);
        changingFile = false;
        dirty = false;
        title.setText("🦅 " + project.getName());
    }

    private void askNewProject() {
        new AlertDialog.Builder(this).setTitle("Proyecto nuevo")
                .setMessage("Se sustituye el proyecto actual en memoria. Guarda primero tus cambios si los necesitas.")
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Crear", (dialog, which) -> {
                    project = PforgeProject.createDemo();
                    selectedFile = null;
                    refreshFiles("main.v");
                    setStatus("Proyecto nuevo. Guárdalo para crear su .pforge.");
                }).show();
    }

    private void askNewSource() {
        EditText name = new EditText(this);
        name.setSingleLine(true);
        name.setText("nuevo.v");
        new AlertDialog.Builder(this)
                .setTitle("Añadir archivo Verilog")
                .setView(name)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Añadir", (dialog, which) -> {
                    try {
                        syncEditor();
                        String filename = name.getText().toString().trim();
                        project.addSource(filename, "module nuevo;\nendmodule\n");
                        refreshFiles(filename);
                        dirty = true;
                        setStatus("Se añadió " + filename + ". Guarda el proyecto.");
                    } catch (IOException error) {
                        showError("Archivo nuevo", error);
                    }
                }).show();
    }

    private void chooseProject() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*"); // Android file providers may not know .pforge MIME.
        startActivityForResult(intent, OPEN_PROJECT);
    }

    private void saveProject() {
        try {
            syncEditor();
            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("application/octet-stream");
            String filename = project.getName().replaceAll("[^a-zA-Z0-9_-]", "_");
            intent.putExtra(Intent.EXTRA_TITLE, (filename.isEmpty() ? "PhoenixForge" : filename) + ".pforge");
            startActivityForResult(intent, SAVE_PROJECT);
        } catch (IOException error) {
            showError("Guardar", error);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        try {
            if (requestCode == OPEN_PROJECT) {
                PforgeProject replacement;
                try (InputStream input = getContentResolver().openInputStream(uri)) {
                    replacement = PforgeProject.read(input);
                }
                project = replacement;
                selectedFile = null;
                refreshFiles(null);
                setStatus("Proyecto importado con checksums SHA-256 validados.");
            } else if (requestCode == SAVE_PROJECT) {
                syncEditor();
                try (OutputStream output = getContentResolver().openOutputStream(uri, "w")) {
                    if (output == null) throw new IOException("El proveedor de archivos no permitió guardar");
                    project.save(output);
                }
                dirty = false;
                setStatus("Proyecto .pforge guardado. Compatible con PhœnixForge Desktop.");
                Toast.makeText(this, "Proyecto guardado", Toast.LENGTH_SHORT).show();
            }
        } catch (Exception error) {
            showError(requestCode == OPEN_PROJECT ? "Abrir proyecto" : "Guardar proyecto", error);
        }
    }

    private void showHdlSummary() {
        try {
            syncEditor();
            String value = selectedFile == null ? "" : project.getSource(selectedFile);
            Pattern pattern = Pattern.compile("\\bmodule\\s+([A-Za-z_][A-Za-z_0-9$]*)");
            Matcher matcher = pattern.matcher(value);
            StringBuilder modules = new StringBuilder();
            int count = 0;
            while (matcher.find() && count < 64) {
                if (count++ > 0) modules.append(", ");
                modules.append(matcher.group(1));
            }
            String info = "Archivo: " + selectedFile +
                    "\nLíneas: " + value.split("\\n", -1).length +
                    "\nMódulos detectados (resumen textual): " +
                    (count == 0 ? "ninguno" : modules.toString()) +
                    "\n\nNo es un parser completo ni una compilación Verilog. La simulación Icarus requiere un motor Android nativo pendiente.";
            new AlertDialog.Builder(this).setTitle("Resumen HDL").setMessage(info)
                    .setPositiveButton("Cerrar", null).show();
        } catch (IOException error) {
            showError("Resumen HDL", error);
        }
    }
}
