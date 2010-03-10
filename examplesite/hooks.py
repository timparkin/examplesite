def pre_flush_hook(request, additions, deletions, changes):
    print 'PRE===='
    print 'additions',additions
    print 'deletions',deletions
    print 'changes',changes

def post_flush_hook(request, additions, deletions, changes):
    print 'POST===='
    print 'additions',additions
    print 'deletions',deletions
    print 'changes...'
    for c in changes:
        print c[0]
        print '#',list(c[1])
