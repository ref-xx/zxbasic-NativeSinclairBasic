# Boriel ZX Basic - Direct

Boriel ZX Basic - Direct is a specialized fork of Boriel's ZX BASIC Compiler designed for direct, out-of-the-box compilation of unmodified Sinclair BASIC programs, with seamless integration for BasinC IDE (https://github.com/ref-xx/basinc).

Boriel's Basic is a Sinclair BASIC-like language, but it is not compatible with Sinclair BASIC. Apart from very simple programs, it cannot compile standard Sinclair BASIC source code without major adjustments. Work on this compiler is ongoing; for programs it can compile successfully, it can provide speed improvements of up to approximately ten times.

---

## Why this Fork?

In upstream Boriel ZX Basic, implicit type inference aggressively defaults small numeric literals (e.g. `let r = 50`) to 8-bit unsigned integers (`ubyte`). While fast, native Sinclair BASIC treats all numbers as 40-bit floating-point values. This often leads to subtle 8-bit math overflow issues (for instance, `50 * 50 = 2500` truncating in 8-bit to `196`, causing `A Invalid argument` on `SQR` calls or corrupting screen calculations).

Moreover, Sinclair BASIC has no syntax like `DIM x AS FLOAT`. To keep legacy Sinclair BASIC programs completely standard and untouched while still gaining high-speed compiled machine code, this fork introduces command-line level semantic controls and metadata filters.

---

## Key Features & New CLI Options

### 1. `--basinc` (BasInc Metadata Filter)
Automatically strips out BasInc project headers and metadata (such as `Check`, `Auto`, `#Note`, `# Run-time Variables ... # End Run-time Variables`, and `Var ` blocks) before compilation.
- **Line number preservation:** Stripped metadata lines are converted into empty blank lines so that all compiler warnings, errors, and line numbers match your source `.bas` file 1:1.

### 2. `--default-float` (Native Sinclair Float Semantics)
Forces all untyped numeric variables to default to Sinclair BASIC's native 40-bit Float instead of Boriel's default 8-bit `ubyte` integer inference.
- Eliminates 8-bit math truncation/overflows without needing to add dialect-specific type annotations into your BASIC code.

### 3. CLI Variable Type Overrides (`--var<type>`)
Allows you to selectively optimize specific variables into fast integers or bytes directly from the command line, without modifying your BASIC source code:
- `--varubyte <v1,v2,...>` (Unsigned 8-bit: `0` to `255`)
- `--varbyte <v1,v2,...>` (Signed 8-bit: `-128` to `127`)
- `--varuinteger <v1,v2,...>` (Unsigned 16-bit: `0` to `65535`)
- `--varinteger <v1,v2,...>` (Signed 16-bit: `-32768` to `32767`)
- `--varulong <v1,v2,...>` (Unsigned 32-bit: `0` to `4294967295`)
- `--varlong <v1,v2,...>` (Signed 32-bit)
- `--varfloat <v1,v2,...>` (ZX Spectrum 40-bit Float)
- `--varfixed <v1,v2,...>` (16.16 Fixed point)

Example strategy: Use `--default-float` to keep all calculations safe, and supply `--varubyte x,y,border` to accelerate inner loops and screen coordinates.

### 4. Standalone Single-File Binary (`zxbc-direct.exe`)
Bundled as a single self-contained executable with the runtime library embedded. No Python installation or separate dependency folders are required to run.

---

## Quick Start & Usage Examples

### 1. Compile a BasInc `.bas` file directly to `.tap`:
```bash
zxbc-direct.exe mygame.bas -f tap --autorun --basinc --default-float
```

### 2. Compile with selective variable acceleration:
```bash
zxbc-direct.exe circleBASINC.bas -f tap --autorun --basinc --default-float --varubyte xc,yc,r --varfloat r2
```

### 3. Generate raw machine code at a specific memory address:
```bash
zxbc-direct.exe routine.bas --org 32768 -f bin -o routine.bin
```

---

## Building from Source

To build the standalone single-file `zxbc-direct.exe` using PyInstaller:

1. Clone this repository:
   ```bash
   git clone https://github.com/ref-xx/zxbasic-NativeSinclairBasic.git
   cd zxbasic-NativeSinclairBasic
   ```
2. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
3. Build the binary using the included spec file:
   ```bash
   pyinstaller zxbc-direct.spec
   ```
   The output binary will be created in the `dist/` directory.

---

## Compatibility

- 100% compatible with existing Boriel ZX Basic compiler options, syntax, inline assembly (`ASM ... END ASM`), and libraries.
- Tested and verified on Windows with Python 3.10+ / PyInstaller.

---

## License & Credits

- Original ZX BASIC Compiler: Copyright (K) 2008 Jose Rodriguez-Rosa (a.k.a. Boriel) (http://www.boriel.com).
- Licensed under the GNU Affero General Public License v3 (AGPL-3.0).
- Compiler runtime library (`library/` and `library-asm/`) is licensed under the MIT License.
- Fork maintained by ref-xx (https://github.com/ref-xx).
