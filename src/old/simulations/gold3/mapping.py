import pickle


class Mapping:
    def __init__(self, nodesSol, edgesSol):
        self.nodesSol = nodesSol
        self.edgesSol = edgesSol

    def save(self, file="mapping.data"):
        with open(file,"w") as f:
            pickle.Pickler(f).dump(self)

    @classmethod
    def fromFile(cls, self, file="mapping.data"):
        with open(file,"r") as f:
            obj = pickle.load(self, file)
            return cls(obj.nodesSol, obj.edgesSol)
