from zerospeech.task_manager.supervisors import Multiprocess, SingleProcess

SUPERVISORS = {f"multiprocess": Multiprocess, f"singleprocess": SingleProcess}


class Config:

    def __init__(self, **kwargs):
        # Supervisor class
        supervisor = kwargs.get("supervisor", "singleprocess")
        self.supervisor_class = SUPERVISORS.get(supervisor)



class Server:
    pass

