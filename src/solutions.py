class Solution:
    def __init__(self):
        with open("solutions.data") as f:
            constraints=filter(lambda x: "master" in x, f.read().split("\n"))
            handle
