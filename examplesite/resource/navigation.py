from datetime import date

from menuish.menu import create_sitemap
from operator import itemgetter




WORKSHOP_CATEGORIES = [('practical','Practical Workshops'),('software','Software Training'),('capture2computer', 'Capture 2 Computer')]




def get_navigation(request):
    segments = request.url.path_segments
    C = request.environ['couchish']
    with C.session() as S:
        pages = list(S.view('page/by_segments'))
    count = 0
    lastparent = []
    sitemap = []
    for page in pages:
        if page.key != [""]:
            key = 'root.' + '.'.join(page.key)
        else:
            key = 'root'
        parent = key.split('.')[:-1]
        if parent == lastparent:
            count += 1
        else:
            count = 1
            lastparent = parent
        node = [key,page.value['title'], count, {}]
        sitemap.append(node)
    return create_sitemap(sitemap)
