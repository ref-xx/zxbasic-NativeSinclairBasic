import os
import tempfile
import unittest

from src.api import global_
from src.api.config import OPTIONS
from src.zxbc import zxbc


class TestStrAnd(unittest.TestCase):
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

    def test_str_and_rejected_in_standard_mode(self):
        code = '10 LET a = 1\n20 PRINT ("testing" AND a=1)\n'
        exit_code, _ = self._compile_code(code, ["--strict"])
        self.assertNotEqual(exit_code, 0)
        self.assertGreater(global_.has_errors, 0)

    def test_str_and_in_sinclair_mode(self):
        code = '10 LET a = 1\n20 PRINT ("testing" AND a=1)\n'
        exit_code, asm = self._compile_code(code, ["--sinclair"])
        self.assertEqual(exit_code, 0)
        self.assertIn("jr nz,", asm)
        self.assertIn("ld hl, 0", asm)
        self.assertIn("__PRINTSTR", asm)

    def test_str_and_in_basinc_mode(self):
        code = '10 LET a = 1\n20 PRINT ("testing" AND a=1)\n'
        exit_code, asm = self._compile_code(code, ["--basinc"])
        self.assertEqual(exit_code, 0)
        self.assertIn("jr nz,", asm)
        self.assertIn("ld hl, 0", asm)
        self.assertIn("__PRINTSTR", asm)

    def test_str_and_with_numeric_condition(self):
        code = '10 LET a = 5\n20 PRINT ("hello" AND a)\n'
        exit_code, asm = self._compile_code(code, ["--sinclair"])
        self.assertEqual(exit_code, 0)
        self.assertIn("jr nz,", asm)
        self.assertIn("ld hl, 0", asm)

    def test_str_and_string_condition_rejected(self):
        code = '10 PRINT ("str1" AND "str2")\n'
        exit_code, _ = self._compile_code(code, ["--sinclair"])
        self.assertNotEqual(exit_code, 0)
        self.assertGreater(global_.has_errors, 0)
