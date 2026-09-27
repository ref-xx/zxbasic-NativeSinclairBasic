import unittest
from src.zxbpp.base_pplex import transform_sinclair_input


class TestSinclairInput(unittest.TestCase):
    def test_numeric_input_simple(self):
        code = "10 INPUT a\n"
        out = transform_sinclair_input(code)
        self.assertIn("LET a = __zxb_input_num()", out)

    def test_string_input_simple(self):
        code = "10 INPUT a$\n"
        out = transform_sinclair_input(code)
        self.assertIn("LET a$ = __zxb_input_str()", out)

    def test_numeric_input_with_prompt(self):
        code = '10 INPUT "Enter age: "; age\n'
        out = transform_sinclair_input(code)
        self.assertIn('PRINT "Enter age: ";: LET age = __zxb_input_num()', out)

    def test_string_input_with_prompt(self):
        code = '10 INPUT "Enter name: "; name$\n'
        out = transform_sinclair_input(code)
        self.assertIn('PRINT "Enter name: ";: LET name$ = __zxb_input_str()', out)

    def test_expression_prompt(self):
        code = '1310 INPUT ("new ";str_b$;"? ");a\n'
        out = transform_sinclair_input(code)
        self.assertIn('PRINT "new ";str_b$;"? ";: LET a = __zxb_input_num()', out)

    def test_array_target(self):
        code = '20 INPUT nary_a(f)\n'
        out = transform_sinclair_input(code)
        self.assertIn('LET nary_a(f) = __zxb_input_num()', out)

    def test_multiple_variables(self):
        code = '30 INPUT a, b\n'
        out = transform_sinclair_input(code)
        self.assertIn('LET a = __zxb_input_num(): LET b = __zxb_input_num()', out)

    def test_line_string_input(self):
        code = '40 INPUT LINE a$\n'
        out = transform_sinclair_input(code)
        self.assertIn('LET a$ = __zxb_input_str()', out)


if __name__ == "__main__":
    unittest.main()
