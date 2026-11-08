// Teaches Ghidra the Watcom register calling convention and applies it to DOOM95.EXE.
//
// DOOM95.EXE was built with Watcom C/C++ using its register convention: the first four
// arguments go in EAX, EDX, EBX, ECX, the rest go on the stack (popped by the callee), and
// the callee preserves every register except the ones holding the return value. Ghidra's
// x86 Windows spec has no such prototype, so without it the decompiler drops arguments
// (M_CheckParm() with no string) and invents extraout_EDX / extraout_ECX variables.
//
// This script:
//   1. adds a "__watcall" prototype to the program as a compiler-spec extension
//      (shown later under Edit > Options for Program > Specification Extensions),
//   2. sets it on every Watcom-convention function from config/symbols.csv:
//        - C functions whose raw name ends in '_'  (M_CheckParm_)
//        - Watcom C++ functions (W?name$...) except Windows callbacks (*Proc, *Callback),
//          which Windows calls with __stdcall
//      C-library varargs functions (printf_, sprintf_, ...) get __cdecl instead.
//      Functions whose signature you edited yourself, or that use custom storage, are skipped.
//   3. re-runs decompiler parameter ID on those functions so Ghidra fills in the parameters.
//
// Run it after ImportDoom95Symbols.java. It can be run again safely.
//@category Doom95
//@menupath Tools.Doom95.Apply Watcom Calling Convention

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import ghidra.app.cmd.function.DecompilerParameterIdCmd;
import ghidra.app.script.GhidraScript;
import ghidra.program.database.SpecExtension;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;

public class ApplyWatcomCallingConvention extends GhidraScript {

    static final String CONVENTION = "__watcall";

    // Watcom C library functions taking "..." keep the trailing '_' but pass every argument on
    // the stack, caller-cleaned. (DOOM's own varargs functions, like I_Error, are named _I_Error
    // instead and are skipped below with the other leading-underscore __cdecl symbols.)
    static final Set<String> VARIADIC_CLIB = new HashSet<>(Arrays.asList(
        "printf_", "sprintf_", "fprintf_", "cprintf_", "scanf_", "sscanf_", "fscanf_", "cscanf_",
        "open_", "sopen_", "execl_", "execlp_", "spawnl_", "spawnlp_"));

    static final String PROTOTYPE_XML =
        "<prototype name=\"" + CONVENTION + "\" extrapop=\"unknown\" stackshift=\"4\">\n" +
        "  <input>\n" +
        "    <pentry minsize=\"1\" maxsize=\"4\"><register name=\"EAX\"/></pentry>\n" +
        "    <pentry minsize=\"1\" maxsize=\"4\"><register name=\"EDX\"/></pentry>\n" +
        "    <pentry minsize=\"1\" maxsize=\"4\"><register name=\"EBX\"/></pentry>\n" +
        "    <pentry minsize=\"1\" maxsize=\"4\"><register name=\"ECX\"/></pentry>\n" +
        "    <pentry minsize=\"1\" maxsize=\"500\" align=\"4\"><addr offset=\"4\" space=\"stack\"/></pentry>\n" +
        "  </input>\n" +
        "  <output killedbycall=\"true\">\n" +
        "    <pentry minsize=\"4\" maxsize=\"10\" metatype=\"float\" extension=\"float\"><register name=\"ST0\"/></pentry>\n" +
        "    <pentry minsize=\"1\" maxsize=\"4\"><register name=\"EAX\"/></pentry>\n" +
        // No EDX:EAX slot: EDX is callee-preserved, so Ghidra would mistake every function for
        // one returning a 64-bit value with its EDX argument in the top half. DOOM has no
        // 64-bit return values (fixed_t is 32-bit), so EAX alone is right.
        "  </output>\n" +
        "  <unaffected>\n" +
        "    <varnode space=\"ram\" offset=\"0\" size=\"4\"/>\n" +
        "    <register name=\"ESP\"/>\n" +
        "    <register name=\"EBP\"/>\n" +
        "    <register name=\"ESI\"/>\n" +
        "    <register name=\"EDI\"/>\n" +
        "    <register name=\"EBX\"/>\n" +
        "    <register name=\"ECX\"/>\n" +
        "    <register name=\"EDX\"/>\n" +
        "    <register name=\"DF\"/>\n" +
        "    <register name=\"FS_OFFSET\"/>\n" +
        "  </unaffected>\n" +
        "  <killedbycall>\n" +
        "    <register name=\"ST0\"/>\n" +
        "    <register name=\"ST1\"/>\n" +
        "  </killedbycall>\n" +
        "</prototype>\n";

    @Override
    protected void run() throws Exception {
        // Headless: pass the CSV path as the script argument. GUI: you're asked for the file.
        String[] args = getScriptArgs();
        File csv = args.length > 0 ? new File(args[0]) : askFile("Select config/symbols.csv", "Apply");

        // 1. Install (or replace) the prototype extension.
        new SpecExtension(currentProgram).addReplaceCompilerSpecExtension(PROTOTYPE_XML, monitor);
        println("Installed calling convention " + CONVENTION);

        // 2. Apply it to the Watcom-convention functions.
        int applied = 0, kept = 0, missing = 0, callbacks = 0, varargs = 0;
        List<String> skippedCallbacks = new ArrayList<>();
        AddressSet toAnalyze = new AddressSet();

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
                if (f.length < 7 || !f[1].equals("code")) {
                    continue;
                }
                String raw = f[4];
                boolean cFunc = raw.endsWith("_") && !raw.startsWith("_");
                boolean cppFunc = raw.startsWith("W?");
                if (!cFunc && !cppFunc) {
                    continue; // __cdecl (_name), __stdcall (_name@N) or runtime/asm symbols
                }
                if (VARIADIC_CLIB.contains(raw)) {
                    Function fn = getFunctionAt(toAddr(Long.parseLong(f[0], 16)));
                    if (fn != null && !fn.hasCustomVariableStorage()
                            && fn.getSignatureSource() != SourceType.USER_DEFINED) {
                        fn.setCallingConvention("__cdecl");
                        fn.setVarArgs(true);
                        fn.setSignatureSource(SourceType.DEFAULT);
                        toAnalyze.add(fn.getEntryPoint());
                        varargs++;
                    }
                    continue;
                }
                if (cppFunc && isWindowsCallback(raw)) {
                    callbacks++;
                    skippedCallbacks.add(raw);
                    continue;
                }

                Address addr = toAddr(Long.parseLong(f[0], 16));
                Function fn = getFunctionAt(addr);
                if (fn == null) {
                    missing++;
                    continue;
                }
                if (fn.hasCustomVariableStorage() || fn.getSignatureSource() == SourceType.USER_DEFINED) {
                    kept++;
                    continue;
                }
                fn.setCallingConvention(CONVENTION);
                // Let parameter ID replace whatever stack-based parameters were guessed before.
                fn.setSignatureSource(SourceType.DEFAULT);
                toAnalyze.add(addr);
                applied++;
            }
        }

        println(String.format(
            "%s set on %d functions; %d C-library varargs functions set to __cdecl; " +
            "%d kept (user-edited or custom storage), %d not functions, %d Windows callbacks left alone",
            CONVENTION, applied, varargs, kept, missing, callbacks));
        for (String cb : skippedCallbacks) {
            println("  callback, left as-is: " + cb);
        }

        // 3. Recover parameters with the new convention.
        if (!toAnalyze.isEmpty()) {
            println("Running decompiler parameter ID on " + toAnalyze.getNumAddressRanges() + " functions...");
            DecompilerParameterIdCmd cmd = new DecompilerParameterIdCmd(
                "Doom95 Watcom parameter ID", toAnalyze, SourceType.ANALYSIS, false, false, 60);
            if (!cmd.applyTo(currentProgram, monitor)) {
                printerr("Parameter ID failed: " + cmd.getStatusMsg());
            }
        }
        println("Done. Reopen any decompiler windows to see the new signatures.");
    }

    // Functions Windows calls back into (window procs, enum callbacks) use __stdcall.
    private static boolean isWindowsCallback(String raw) {
        int end = raw.indexOf('$');
        String name = end > 2 ? raw.substring(2, end) : raw;
        return name.endsWith("Proc") || name.endsWith("Callback");
    }
}
