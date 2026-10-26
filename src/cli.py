from prompt_toolkit import prompt
from rich.console import Console
from rich.markdown import Markdown



class Cli:
    def __init__(self):
        self._concole=Console()
    def read_prompt(self,out:str=None)->str:
        text=prompt(out,multiline=True)
        print("\n")
        return text
    def show_answer(self,answer:str)->str:
        self._concole.print(Markdown(answer))
        print("\n")
        self._concole.print(Markdown("---"))

#cli=Cli()
#breakpoint()