def get_ticker(rs,x):
    def ticker():
        return rs.poisson(x, 1)[0]

    return ticker



