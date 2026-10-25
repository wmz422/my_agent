
class Session:
    def __init__(self,system_prompt):
        self.history=list()
        self.history.append({'role': 'system', 'content': system_prompt})

