def get_content_generator(rs, param):
    def draw():
        return rs.zipf(param)

    return draw


