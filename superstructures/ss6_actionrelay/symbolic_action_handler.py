class SymbolicActionHandler:
    def __init__(self):
        self.actions = {}

    def register_action(self, action_name, handler):
        if action_name in self.actions:
            raise ValueError(f"Action '{action_name}' is already registered.")
        self.actions[action_name] = handler

    def execute_action(self, action_name, *args, **kwargs):
        if action_name not in self.actions:
            raise ValueError(f"Action '{action_name}' is not registered.")
        return self.actions[action_name](*args, **kwargs)

    def list_actions(self):
        return list(self.actions.keys())