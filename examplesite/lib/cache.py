def key(*var):
    if len(var) == 1:
        return replace_none(var[0])
    return '\u0000'.join([replace_none(segment) for segment in var])

def replace_none(d):
    if d is None:
        return '<none>'
    else:
        return d

