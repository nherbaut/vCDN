import pickle


class Mapping:
    def __init__(self, nodesSol, edgesSol, objective_function, violations=[]):
        self.nodesSol = nodesSol
        self.edgesSol = edgesSol
        self.objective_function = objective_function
        self.violations = violations

    def save(self, file="mapping.data"):
        with open(file, "w") as f:
            pickle.Pickler(f).dump(self)

    def get_vhg_mapping(self):
        return filter(lambda x: "VHG" in x[1], self.nodesSol)

    @classmethod
    def fromFile(cls, self, file="mapping.data"):
        with open(file, "r") as f:
            obj = pickle.load(self, file)
            return cls(obj.nodesSol, obj.edgesSol)
