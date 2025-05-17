import unittest
from symbolic_action_handler import SymbolicActionHandler

class TestSymbolicActionHandler(unittest.TestCase):

    def setUp(self):
        self.handler = SymbolicActionHandler()

    def test_register_action(self):
        def sample_action():
            return "Action executed"

        self.handler.register_action("sample", sample_action)
        self.assertIn("sample", self.handler.list_actions())

    def test_execute_action(self):
        def sample_action():
            return "Action executed"

        self.handler.register_action("sample", sample_action)
        result = self.handler.execute_action("sample")
        self.assertEqual(result, "Action executed")

    def test_list_actions(self):
        def action_one():
            pass

        def action_two():
            pass

        self.handler.register_action("action_one", action_one)
        self.handler.register_action("action_two", action_two)
        actions = self.handler.list_actions()
        self.assertIn("action_one", actions)
        self.assertIn("action_two", actions)

    def test_register_duplicate_action(self):
        def sample_action():
            pass

        self.handler.register_action("sample", sample_action)
        with self.assertRaises(ValueError):
            self.handler.register_action("sample", sample_action)

if __name__ == "__main__":
    unittest.main()