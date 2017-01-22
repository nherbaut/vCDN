def get_ticker(x, rs):
    def ticker():
        return rs.poisson(x, 1)[0]
    return ticker



