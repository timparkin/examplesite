from __future__ import with_statement
from adminish import markdown, mdx_enhanced_image

from restish import url
from breve.tags.html import tags as T
from breve.flatten import flatten

from restish import templating


def make_product(request, line):
    code = line.strip()
    C = request.environ['couchish']
    with C.session() as S:
        product = S.doc_by_view('product/by_code',key=code)
    data = {'request': request, 'product': product}
    out = templating.render(request, 'shop/product-fragment.html', data, encoding='utf8')
    return out

    

processors = {
  'PRODUCT': make_product,
        }


def process(request, line):
    command, args = line[1:].split('@',1)
    if command not in processors:
        return line
    out = processors[command](request, args)
    return out

def md(request, text):
    out = []
    for line in text.splitlines():
        if line.startswith('@'):
            line = process(request, line)
        out.append(line)
    text = '\n'.join(out)
    return markdown.markdown(text, [mdx_enhanced_image])

