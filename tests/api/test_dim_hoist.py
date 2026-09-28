import unittest
from src.api import global_
from src.zxbpp.base_pplex import transform_hoist_sinclair_dims


class TestDimHoist(unittest.TestCase):
    def setUp(self):
        global_.has_errors = 0
        global_.error_msg_cache.clear()

    def test_simple_dim_hoisting(self):
        code = "10 DIM a(10)\n20 PRINT a(1)\n"
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertTrue(out.startswith("DIM a(10)\n#line 1 \"test.bas\"\n"))
        self.assertIn("10 REM [hoisted] DIM a(10)", out)
        self.assertIn("20 PRINT a(1)", out)
        self.assertEqual(global_.has_errors, 0)

    def test_multi_dim_line_with_code(self):
        code = "9020 DIM z(30): DIM nary_a(4): DIM nary_b(4): LET nary_a(1)=20\n"
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertIn("DIM z(30): DIM nary_a(4): DIM nary_b(4)", out)
        self.assertIn("9020 LET nary_a(1)=20", out)
        self.assertEqual(global_.has_errors, 0)

    def test_multi_variable_dim(self):
        code = "100 DIM x(5), y(10)\n"
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertIn("DIM x(5): DIM y(10)", out)
        self.assertIn("100 REM [hoisted] DIM x(5), y(10)", out)
        self.assertEqual(global_.has_errors, 0)

    def test_redim_error(self):
        code = "10 DIM a(10)\n20 LET a(1)=1\n50 DIM a(20)\n"
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertGreater(global_.has_errors, 0)
        # Error should mention 'a' and previous location
        cached = list(global_.error_msg_cache)
        self.assertTrue(any("already dimensioned" in msg and "'a'" in msg for msg in cached))

    def test_redim_same_line_error(self):
        code = "10 DIM a(10), a(20)\n"
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertGreater(global_.has_errors, 0)
        cached = list(global_.error_msg_cache)
        self.assertTrue(any("already dimensioned" in msg and "'a'" in msg for msg in cached))

    def test_quotes_and_rem_ignored(self):
        code = '10 PRINT "DIM a(10)": REM DIM b(20)\n'
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertEqual(out, code)
        self.assertEqual(global_.has_errors, 0)

    def test_typed_dim(self):
        code = "10 DIM a(10) AS INTEGER\n"
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertIn("DIM a(10) AS INTEGER", out)
        self.assertEqual(global_.has_errors, 0)

    def test_no_dim(self):
        code = "10 PRINT 1\n20 PRINT 2\n"
        out = transform_hoist_sinclair_dims(code, "test.bas")
        self.assertEqual(out, code)
        self.assertEqual(global_.has_errors, 0)


if __name__ == "__main__":
    unittest.main()
