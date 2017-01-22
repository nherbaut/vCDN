def get_content_generator(rs, param, contentHistory):
    def draw():
        content = rs.zipf(param)
        contentHistory.push(content)
        return content

    return draw
