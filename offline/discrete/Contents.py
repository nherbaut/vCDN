def get_content_generator(rs, param, contentHistory, bw, cap, duration):
    def draw():
        content = rs.zipf(param)
        contentHistory.push(content)
        return content, bw, cap, duration

    return draw
