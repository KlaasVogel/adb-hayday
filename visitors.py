from hd import HD
from time import sleep

class Visitors(list):
    def __init__(self, device, tasklist):
        for i in range(3):
            self.append(Visitor(divice, tasklist, f"visit{i}"))


class Visitor(HD):
    def __init__(self, device, tasklist, name):
        HD.__init__(self, device, tasklist, name)
        self.templates=HD.loadTemplates('visitors',name)
    
