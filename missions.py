from dataclasses import dataclass,field
from typing import List,Optional

@dataclass
class Mission:
    id:str; title:str; steps:List[str]
    step:int=0; done:bool=False
    def advance(self):
        self.step+=1
        if self.step>=len(self.steps): self.done=True
    def text(self)->str:
        if self.done: return "Complete"
        return self.steps[self.step] if self.step<len(self.steps) else ""

class MissionManager:
    def __init__(self):
        self.active:Optional[str]=None
        self.M:dict={
            'terminal':  Mission('terminal','Morning Routine',["Check the Stock Market Terminal"]),
            'go_academy':Mission('go_academy','Academy Bound',
                ["Exit your apartment","Reach your Flying Scooty","Arrive at Ad-itya Sam Rocks Academy"]),
            'find_lab':  Mission('find_lab','The Research Lab',["Find Suzen and Reza in the Lab"]),
            'escape':    Mission('escape','Escape — 2026',
                ["Find exit from the school","Reach the rooftop","Escape"]),
            'repair':    Mission('repair','Repair Time Machine',
                ["Reconnect power circuits","Calibrate energy core","Attempt reconnection"]),
            'shelter':   Mission('shelter','Find Shelter',
                ["Explore the 2026 streets","Find a place to rest"]),
        }
    def set(self,mid:str): self.active=mid
    def advance(self):
        if self.active and self.active in self.M:
            self.M[self.active].advance()
            if self.M[self.active].done: self.active=None
    def text(self)->str:
        if self.active and self.active in self.M: return self.M[self.active].text()
        return ""
    def title(self)->str:
        if self.active and self.active in self.M: return self.M[self.active].title
        return ""
    def is_done(self,mid:str)->bool:
        return self.M[mid].done if mid in self.M else False