class Solution:
    def __init__(self):
        with open("solutions.data") as f:
            constraints=[x for x in f.read().split("\n") if "master" in x]

