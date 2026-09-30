import unittest
import tempfile
import os
from src.api.config import OPTIONS
from src.api import global_
from src.zxbpp.base_pplex import transform_hoist_sinclair_dims
from src.zxbc import zxbc


class TestVarTypes(unittest.TestCase):
    def setUp(self):
        global_.has_errors = 0
        global_.error_msg_cache.clear()
        OPTIONS.var_types = {}

    def tearDown(self):
        OPTIONS.var_types = {}

    def test_hoist_with_var_types(self):
        OPTIONS.var_types = {"c": "integer", "b": "byte"}
        code = "10 DIM c(21, 3): DIM b(4, 9)\n20 LET c(1, 1)=5\n"
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertIn("DIM c(21, 3) AS INTEGER", out)
        self.assertIn("DIM b(4, 9) AS BYTE", out)
        self.assertEqual(global_.has_errors, 0)

    def test_compile_array_and_var_with_var_types(self):
        code = """10 DIM c(10): LET timer=9999
20 LET c(1)=100: LET timer=timer-1
30 PRINT c(1); timer
"""
        with tempfile.NamedTemporaryFile("w", suffix=".bas", delete=False) as f:
            f.write(code)
            src_name = f.name
        bin_name = src_name + ".bin"

        try:
            # Test compiling with --basinc and --varinteger c,timer
            argv = [
                src_name,
                "-f", "bin",
                "--basinc",
                "-Z",
                "--default-float",
                "--varinteger", "c,timer",
                "-o", bin_name,
            ]
            ret = zxbc.main(argv)
            self.assertEqual(ret, 0)
            self.assertEqual(global_.has_errors, 0)
            self.assertTrue(os.path.exists(bin_name))
        finally:
            if os.path.exists(src_name):
                os.remove(src_name)
            if os.path.exists(bin_name):
                os.remove(bin_name)
