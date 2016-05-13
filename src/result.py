class ResultItem:
    def __init__(self, substrate, success, success_rate, service, mapping):
        self.substrate = substrate
        self.success = success
        self.success_rate = success_rate
        self.service = service
        self.mapping = mapping
        self.marker =  " "
        self.linestyle = "solid"
