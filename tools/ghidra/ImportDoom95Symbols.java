// Applies the original DOOM95.EXE symbol names (from config/symbols.csv) to the open program.
// The CSV is produced by tools/watcom_syms.py from the Watcom debug info left in the executable.
// Code symbols become functions with a plate comment naming their source file;
// data symbols become labels. Existing user-defined names are left alone.
//@category Doom95
//@menupath Tools.Doom95.Import Original Symbols

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.HashSet;
import java.util.Set;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.symbol.Symbol;

public class ImportDoom95Symbols extends GhidraScript {

    @Override
    protected void run() throws Exception {
        // Headless: pass the CSV path as the script argument. GUI: you're asked for the file.
        String[] args = getScriptArgs();
        File csv = args.length > 0 ? new File(args[0]) : askFile("Select doom95_symbols.csv", "Import");

        int functions = 0, renamed = 0, labels = 0, skipped = 0, failed = 0;
        Set<String> seenAddresses = new HashSet<>();

        try (BufferedReader in = new BufferedReader(new FileReader(csv))) {
            String header = in.readLine();
            if (header == null || !header.startsWith("address,type,static,name,raw_name,section,source")) {
                printerr("Unexpected CSV header: " + header);
                return;
            }
            String line;
            while ((line = in.readLine()) != null) {
                monitor.checkCancelled();
                String[] f = line.split(",", 7);
                if (f.length < 7) {
                    continue;
                }
                Address addr = toAddr(Long.parseLong(f[0], 16));
                boolean isCode = f[1].equals("code");
                String name = f[3];
                String rawName = f[4];
                String source = f[6];
                // Several names can share one address (aliases): the first becomes primary.
                boolean primary = seenAddresses.add(f[0]);

                try {
                    if (isCode && primary) {
                        Function fn = getFunctionAt(addr);
                        if (fn == null) {
                            disassemble(addr);
                            fn = createFunction(addr, name);
                            if (fn == null) {
                                // Keep the name even if Ghidra can't make a function here.
                                createLabel(addr, name, true, SourceType.IMPORTED);
                                failed++;
                                println("Could not create function at " + addr + " (" + name + "), added label");
                                continue;
                            }
                            functions++;
                        } else if (fn.getSymbol().getSource() == SourceType.USER_DEFINED) {
                            skipped++;
                        } else {
                            fn.setName(name, SourceType.IMPORTED);
                            renamed++;
                        }
                        String comment = "Original symbol: " + rawName + "\nSource: " + source;
                        if (getPlateComment(addr) == null) {
                            setPlateComment(addr, comment);
                        }
                    } else {
                        Symbol existing = getSymbolAt(addr);
                        boolean makePrimary = primary && (existing == null
                                || existing.getSource() != SourceType.USER_DEFINED);
                        createLabel(addr, name, makePrimary, SourceType.IMPORTED);
                        labels++;
                    }
                } catch (Exception e) {
                    failed++;
                    println("Failed at " + addr + " (" + name + "): " + e.getMessage());
                }
            }
        }

        println(String.format(
            "Doom95 symbols: %d functions created, %d renamed, %d labels, %d kept (user-named), %d label-only (no function)",
            functions, renamed, labels, skipped, failed));
    }
}
