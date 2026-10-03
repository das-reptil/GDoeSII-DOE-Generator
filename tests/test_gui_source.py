import ast
from pathlib import Path
import unittest


class GuiSourceTests(unittest.TestCase):
    def test_gui_does_not_reference_undefined_nsw_constant(self):
        source_path = Path(__file__).resolve().parents[1] / "src" / "GDoeSII_DOE_Generator.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertNotIn("NSW", names)


if __name__ == "__main__":
    unittest.main()
