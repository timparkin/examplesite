import re

def strip_html(ctx, v):
    v = re.sub(r'<[^>]*?>', '', v)
    return v

def strfprice(ctx, p, strip_pence=False):
    if p == '':
        return ''
    sp = '%0.2f'%(float(p))
    if float(p) > 999:
        sp = '%s,%s'%(sp[:-6],sp[-6:])
    if strip_pence is True and sp[-3:] == '.00':
        return '%s'%sp[:-3]
    return sp

def strford(ctx, d, f):
    if d is None:
        return ''
    if 4 <= d.day <= 20 or 24 <= d.day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][d.day % 10 - 1]
    if f == 'd':
        return '%s%s'%(d.day, suffix)
    if f == 'dm':
        return '%s %s'%(d.day, d.strftime('%B'))
    return '%s%s %s'%(d.day, suffix, d.strftime('%B %Y'))

def strfrange(ctx, f,t):
    if f is None or t is None:
        return ''
    if f.year == t.year:
        if f.month == t.month:
            return '%s - %s of %s'%(strford(ctx,f,'d'), strford(ctx,t,'d'), f.strftime('%B \'%y'))
        return '%s to %s %s'%(strford(ctx,f,'dm'), strford(ctx,t,'dm'), f.strftime('\'%y'))
    return '%s to %s'%(strford(ctx,f,'dmy'), strford(ctx,t,'dmy'))

def get_size_tuple(ctx, product, option):
    photo = product['photo']
    size = option['label'].split(' ')[0]
    size = size.replace('X','x')
    long, short = size.split('x')
    long = int(long[:-1])
    short = int(short[:-1])
    return (long, short), '%0.0f'%float(long), '%0.0f'%(float(short))
