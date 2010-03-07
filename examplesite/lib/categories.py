

def get_parent(segments):
    if len(segments) == 1:
        return ''
    else:
        return '.'.join(segments[:-1])

def mktree(categories):
    cats = list(categories)
    cats.sort(lambda x, y: cmp(len(x['path'].split('.')), len(y['path'].split('.'))))

    last_segments_len = 1
    root = {'': {'data':('root', 'Root'), 'children':[]} }
    for c in cats:
        id = c['path']
        label = c['data']['label']
        segments = id.split('.')
        parent = get_parent(segments)
        root[id] = {'data': (id, label), 'children':[]}
        root[parent]['children'].append(root[id])
    return root['']


def get_label_by_category(flatcats, category):
    label = []
    for c in flatcats:
        path = c['path']
        if category.startswith(path):
            label.append( c['data']['label'] )
    return ', '.join(label)


