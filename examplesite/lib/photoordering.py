import random, copy

def isLarge(photo):
    if photo.aspectratio >1.5:
        return True

def isMedium(photo):
    if photo.aspectratio >=1 and photo.aspectratio <= 1.5:
        return True
    
def isSmall(photo):
    if photo.aspectratio < 1:
        return True


#def isLarge(photo):
    #if photo == 3:
        #return True

#def isMedium(photo):
    #if photo == 2:
        #return True
    
#def isSmall(photo):
    #if photo == 1:
        #return True

class Photo:
    
    def __init__(self,list, photo):
        self.photo = photo
        self.list = list
        if hasattr(photo['photo'], 'metadata'):
            metadata = photo['photo'].metadata
        elif 'metadata' in photo['photo']:
            metadata = photo['photo']['metadata']
        else:
            metadata = photo['photo']['photo']['metadata']
        self.aspectratio = float(metadata['width'])/metadata['height']
        if isLarge(self):
            self.type = 'L'
            self.ascii = '####'
        if isMedium(self):
            self.type = 'M'
            self.ascii = '##'
        if isSmall(self):
            self.type = 'S'
            self.ascii = '#'
            
    @property
    def photodict(self):
        if 'metadata' in self.photo['photo']:
            if hasattr(self.photo,'__subject__'):
                return self.photo.__subject__
            return self.photo
        photo = self.photo['photo']
        out = {}
        out['metadata'] = photo.metadata
        out['filename'] = photo.filename
        out['id'] = photo.id
        out['doc_id'] = photo.doc_id
        self.photo['photo'] = out
        print 'type',type(self.photo)
        return self.photo.__subject__

    def remove(self):
        #print 'popping %s at 0'%(self.list.photos[0].type)
        out = [self.list.photos[0]]
        self.list.photos = self.list.photos[1:]
        return out
        
    def removeWith(self,items):
        photos = copy.copy(self.list.photos)
        out = []
        #print 'popping %s at 0'%(photos[0].type)
        out.append(photos[0])
        photos = photos[1:]
        for s in items:
            for n, photo in enumerate(photos):
                if photo.type == s:
                    #print 'popping %s at %s'%(s,n)
                    out.append(photo)
                    photos.pop(n)
                    break
            else:
                #print 'could not match'
                raise IndexError
        
        #print 'success!'
        self.list.photos = photos
        return out
            
    def __repr__(self):
        return '"%r"'%self.photo
    
class PhotoList:
    
    
    def __init__(self):
        self.photos = []
        self.lastMS = True

    def add(self, photos):
        for photo in photos:
            #print 'type',type(photo)
            self.photos.append( Photo(self, photo) ) 
    
    def process2(self):
        pkeys = ['SSS','MM','MS','SM','L','SS','M','S']
        preferred= {
            'SSS': ['MM','L','MS','SM','SSS','SS','M','S'],
            'MM':  ['SSS','L','SM','MS','MM','SS','M','S'],
            'MS':  ['L','MM','SM','MS','SSS','SS','M','S'],
            'SM':  ['L','MM','MS','SM','SSS','SS','M','S'],
            'L':   ['MM','MS','SM','L','SSS','SS','M','S'],
            'SS':  ['L','MM','MS','SM','SSS','SS','M','S'],
            'M':   ['L','MM','MS','SM','SSS','SS','M','S'],
            'S':   ['L','MM','MS','SM','SSS','SS','M','S'],
            }
            
        out = []
        last = 'MM'
        while(len(self.photos) > 0):

                    
            photo = self.photos[0]
            #print 'currently processing %s of %s'%(photo, self.photos)
            r = None
            #print 'building mp from last %s and first letter %s'%(last,photo.type)
            matchingPreferred = [m for m in preferred[last] if m[0] == photo.type]
            #print 'trying to match one of %s'%matchingPreferred
            for p in matchingPreferred:
                #print 'trying to find %s'%p
                try:
                    if len(p) > 1:
                        #print 'trying to removeWith %s'%''.join(p[1:])
                        r = photo.removeWith( ''.join(p[1:]) )
                        #print 'comment',last, p, r
                        if (last == 'MS' and p == 'MS') or (last == 'SM' and p == 'SM') or (last == 'MM' and p == 'MS'):
                            #print 'swapping'
                            r[0], r[1] = r[1], r[0]
                            #print 'after swap',last, p, r
                            

                    else:
                        #print 'trying to remove'
                        r = photo.remove() 
                    last = ''.join([x.type for x in r])
                    break
                except IndexError:
                    pass
                    #print 'remaining is %s'%self.photos
            if r is not None:
                #print 'adding ',r, 'photos is',self.photos
                out.append(r)
            
        pages = []  
        rows = 0
        for row in out:
            rows += 1
            page = []
            photo = row.photodict
            page.append(photo)
            if rows == 3:
                pages.append(page)
                rows = 0
            
            
        return pages
    
    def process(self, rowsPerPage=3):
        L = [p for p in self.photos if p.type == 'L']
        M = [p for p in self.photos if p.type == 'M']
        S = [p for p in self.photos if p.type == 'S']
        
        nL = len(L)
        nM = len(M)
        nS = len(S)
        #print 'L %s, M %s, S %s'%(nL,nM,nS)
        num_L = nL
        if nM >= nS:
            num_M = nM-nS
            num_MS = nS
            num_SSS = 0
            num_SS = 0
            num_S = 0
        else:
            num_M = 0
            num_MS = nM
            num_SSS = divmod(nS-nM,3)[0]
            if divmod(nS-nM,3)[1] == 2:
                num_SS = 1
                num_S = 0
            elif divmod(nS-nM,3)[1] == 1:
                num_SS = 0
                num_S = 1
            else:
                num_SS = 0
                num_S = 0
    
        #print 'L',num_L
        #print 'MS',num_MS
        #print 'M',num_M
        #print 'SSS',num_SSS
        #print 'SS',num_SS
        #print 'S',num_S
    
        rows = 0
        out = []
        while len(self.photos) > 0:
            rows += 1
            photo = self.photos[0]
            if photo.type == 'L':
                out.append(photo.remove())
                num_L -= 1
                #print '####'
            elif photo.type == 'M':
                if num_MS > 0:
                    r = photo.removeWith('S')
                    num_MS -= 1
                    if self.lastMS:
                        #print '## #'
                        self.lastMS = False
                    else:
                        #print '# ##'
                        self.lastMS = True
                        r.reverse()
                    out.append(r)
                else:
                    num_S -= 1
                    #print '##'
                    out.append(photo.remove())
            elif photo.type == 'S':
                #### to Get a better layout we might randomise this photo extraction ??? (i.e. change the order of the if statements...
                if num_MS > 0:
                    r = photo.removeWith('M')
                    num_MS -= 1
                    if self.lastMS:
                        #print '## #'
                        self.lastMS = False
                        r.reverse()
                    else:
                        #print '# ##'
                        self.lastMS = True
                    out.append(r)
                elif num_SSS > 0:
                    out.append(photo.removeWith('SS'))
                    num_SSS -= 1
                    self.lastMS = True
                    #print '# # #'
                elif num_SS > 0:
                    out.append(photo.removeWith('S'))
                    num_SS -= 1
                    #print '# #'
                else:
                    out.append(photo.remove())
                    num_S -=1
                    #print '#'
            continue
                    
        return out

    
if __name__ == '__main__':
    amount = random.randrange(8,20)
    photos = [random.choice([1,1,1,1,1,1,1,1,1,1,2,2,2,2,3]) for n in xrange(amount)]
    print photos
    photolist = PhotoList()
    photolist.add( photos )
        
    print 'photos ,',[p.type for p in photolist.photos]
            
    ordered_photos = photolist.process2()
    
    
    for p in ordered_photos:
        print ' '.join([r.ascii for r in p])
            
    
    
    
        

