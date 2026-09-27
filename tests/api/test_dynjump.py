# --------------------------------------------------------------------
# Test dynamic jump tables and dynamic restore
# --------------------------------------------------------------------

import unittest

from src.zxbc.args_config import is_line_in_ranges, normalize_dynamic_table_args, parse_line_ranges


class TestDynJump(unittest.TestCase):
    def test_normalize_args(self):
        self.assertEqual(
            normalize_dynamic_table_args(["--enablejumptables", "prog.bas"]),
            ["--enablejumptables=all", "prog.bas"],
        )
        self.assertEqual(
            normalize_dynamic_table_args(["--enablejumptables", "7000-7300,", "9000-9999", "prog.bas"]),
            ["--enablejumptables=7000-7300,,9000-9999", "prog.bas"],
        )
        self.assertEqual(
            normalize_dynamic_table_args(
                ["--enablejumptables", "7000-7300", "--enabledynamicrestore", "8000-9000", "prog.bas"]
            ),
            ["--enablejumptables=7000-7300", "--enabledynamicrestore=8000-9000", "prog.bas"],
        )
        self.assertEqual(
            normalize_dynamic_table_args(["--enablejumptables", "--enabledynamicrestore", "prog.bas"]),
            ["--enablejumptables=all", "--enabledynamicrestore=all", "prog.bas"],
        )

    def test_parse_line_ranges(self):
        self.assertIsNone(parse_line_ranges(None))
        self.assertIsNone(parse_line_ranges("all"))
        self.assertIsNone(parse_line_ranges("ALL"))
        self.assertEqual(parse_line_ranges("7000-7300"), [(7000, 7300)])
        self.assertEqual(parse_line_ranges("7000-7300, 9000-9999"), [(7000, 7300), (9000, 9999)])
        self.assertEqual(parse_line_ranges("500"), [(500, 500)])

    def test_is_line_in_ranges(self):
        self.assertTrue(is_line_in_ranges(7100, None))
        ranges = [(7000, 7300), (9000, 9999)]
        self.assertTrue(is_line_in_ranges(7000, ranges))
        self.assertTrue(is_line_in_ranges(7200, ranges))
        self.assertTrue(is_line_in_ranges(7300, ranges))
        self.assertFalse(is_line_in_ranges(7301, ranges))
        self.assertFalse(is_line_in_ranges(8000, ranges))
        self.assertTrue(is_line_in_ranges(9500, ranges))


if __name__ == "__main__":
    unittest.main()
