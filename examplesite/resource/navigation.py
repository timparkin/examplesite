from datetime import date

from menuish.menu import create_sitemap
from operator import itemgetter






def get_navigation(request):
    segments = request.url.path_segments
    C = request.environ['couchish']
    with C.session() as S:
        pages = list(S.view('page/by_segments'))
        #allpages = list(S.view('page/by_segments'))
    #pages = [p for p in allpages if p.get('sort')] 
    #pages.sort(cmp=lambda x,y: cmp(x.get('sort',9999), y.get('sort',9999)), reverse=True)
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
