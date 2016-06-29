import pickle
import os

RESULTS_FOLDER=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../results')

class Mapping:
    def __init__(self, nodesSol, edgesSol, objective_function, violations=[]):
        self.nodesSol = nodesSol
        self.edgesSol = edgesSol
        self.objective_function = objective_function
        self.violations = violations

    def write(self):
        self.save()

    def save(self, file="mapping",id="default"):
        with open(os.path.join(RESULTS_FOLDER,file+"_"+id), "w") as f:
            pickle.Pickler(f).dump(self)

    def get_vhg_mapping(self):
        return filter(lambda x: "VHG" in x[1], self.nodesSol)

    @classmethod
    def fromFile(cls, self, file="mapping_default.pickle"):
        with open(os.path.join(RESULTS_FOLDER,file), "r") as f:
            obj = pickle.load(self, file)
            return cls(obj.nodesSol, obj.edgesSol)
