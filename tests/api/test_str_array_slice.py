import os
import tempfile
import unittest

from src.api import global_
from src.api.config import OPTIONS
from src.zxbc import zxbc
from src.zxbpp.base_pplex import transform_sinclair_string_arrays


class TestStrArraySlice(unittest.TestCase):
    def setUp(self):
        global_.has_errors = 0
        global_.error_msg_cache.clear()
        self.orig_sinclair = OPTIONS.sinclair
        self.orig_basinc = getattr(OPTIONS, "basinc", False)
        self.orig_filename = getattr(global_, "FILENAME", "(stdin)")

    def tearDown(self):
        global_.FILENAME = self.orig_filename
        OPTIONS.sinclair = self.orig_sinclair
        OPTIONS.basinc = self.orig_basinc

    def _compile_code(self, code: str, flags: list[str]) -> tuple[int, str]:
        with tempfile.NamedTemporaryFile("w", suffix=".bas", delete=False) as bas_f:
            bas_f.write(code)
            bas_name = bas_f.name

        out_name = bas_name + ".asm"
        try:
            cmd = flags + ["-f", "asm", "-o", out_name, bas_name]
            exit_code = zxbc.main(cmd)
            asm_content = ""
            if os.path.exists(out_name):
                with open(out_name, "r", encoding="utf-8") as f:
                    asm_content = f.read()
            return exit_code, asm_content
        finally:
            for p in (bas_name, out_name):
                if os.path.exists(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    def test_unit_transforms(self):
        test_cases = [
            # 1. 2D array slice
            ('10 DIM s$(21, 32)\n20 PRINT s$(x, 1 TO 32)',
             '10 DIM s$(21, 32)\n20 PRINT s$(x)(1 TO 32)'),
            # 2. 2D array single character
            ('10 DIM s$(21, 32)\n20 LET s$(x, y) = "A"',
             '10 DIM s$(21, 32)\n20 LET s$(x)(y) = "A"'),
            # 3. READ with slice
            ('10 DIM s$(21, 32)\n20 READ s$(x, 1 TO 32)',
             '10 DIM s$(21, 32)\n20 READ s$(x)'),
            # 4. In IF condition
            ('10 DIM s$(21, 32)\n20 IF s$(hy+2, hx+1 TO hx+1)="B" THEN LET jump=1',
             '10 DIM s$(21, 32)\n20 IF s$(hy+2)(hx+1 TO hx+1)="B" THEN LET jump=1'),
            # 5. Whole string access (1 arg)
            ('10 DIM s$(21, 32)\n20 PRINT s$(x)',
             '10 DIM s$(21, 32)\n20 PRINT s$(x)'),
            # 6. Inside quotes
            ('10 DIM s$(21, 32)\n20 PRINT "s$(x, 1 TO 32)"',
             '10 DIM s$(21, 32)\n20 PRINT "s$(x, 1 TO 32)"'),
            # 7. REM comment
            ('10 DIM s$(21, 32)\n20 REM s$(x, 1 TO 32)',
             '10 DIM s$(21, 32)\n20 REM s$(x, 1 TO 32)'),
            # 8. DATA statement
            ('10 DATA s$(x, 1 TO 32), 123',
             '10 DATA s$(x, 1 TO 32), 123'),
        ]
        for i, (inp, expected) in enumerate(test_cases, 1):
            out = transform_sinclair_string_arrays(inp)
            self.assertEqual(out.strip(), expected.strip(), f"Test case {i} failed")

    def test_str_array_slice_compiles(self):
        code = '10 DIM s$(21, 32)\n20 LET x = 1\n30 PRINT AT x-1, 0; s$(x, 1 TO 32)\n'
        exit_code, asm = self._compile_code(code, ["--basinc"])
        self.assertEqual(exit_code, 0)
        self.assertIn("__PRINTSTR", asm)

    def test_str_array_char_index_compiles(self):
        code = '10 DIM s$(21, 32)\n20 LET s$(1, 2) = "A"\n30 PRINT s$(1, 2)\n'
        exit_code, asm = self._compile_code(code, ["--basinc"])
        self.assertEqual(exit_code, 0)
        self.assertIn("__PRINTSTR", asm)

    def test_str_array_read_with_slice_compiles(self):
        code = '10 DIM s$(21, 32)\n20 LET x = 1\n30 READ s$(x, 1 TO 32)\n40 DATA "12345678901234567890123456789012"\n'
        exit_code, asm = self._compile_code(code, ["--basinc"])
        self.assertEqual(exit_code, 0)

    def test_str_array_slice_in_if_compiles(self):
        code = '10 DIM s$(21, 32)\n20 LET hy = 1: LET hx = 1\n30 IF s$(hy+2, hx+1 TO hx+1)="B" THEN PRINT "OK"\n'
        exit_code, asm = self._compile_code(code, ["--basinc"])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
