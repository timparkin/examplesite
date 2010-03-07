from __future__ import with_statement
import logging
from restish import http, resource, templating

from examplesite.lib import base, guard

import csv, sys, codecs
from cStringIO import StringIO

import formish, schemaish
from validatish import validator
from formish.fileresource import FileResource
from formish.filestore import CachedTempFilestore, FileSystemHeaderedFilestore
import couchish
from examplesite.lib.filestore import CouchDBAttachmentSource
from wsgiapptools import flash


from operator import itemgetter

log = logging.getLogger(__name__)

CSVPHOTOKEYS = ['code', 'photographer', 'title', 'location']
# ['available', 'first_available', 'code', 'show', '_rev', 'title', 'number', 'collection', 'edition', 'ap_available', 'multiplier', 'model_type', 'information', '_id', 'type']
CSVPRODUCTKEYS = ['change','code','title', 'show', 'available', 'type']
CSVOPTIONKEYS = ['marker','option','label','price','postage']
CSVUSERKEYS = ['email', 'title', 'last_name', 'first_names', 'telephone', 'available', 'type']

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([unicode(s).encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class UnicodeDictReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)
        self.fieldnames = self.reader.next()

    def next(self):
        row = self.reader.next()
        return dict([(f, unicode(row[n], "utf-8")) for n,f in enumerate(self.fieldnames)])

    def __iter__(self):
        return self

class UnicodeDictWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", fieldnames=None, allow_missing_data=False,  **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()
        self.fieldnames = fieldnames
        self.allow_missing_data = allow_missing_data

    def writerow(self, row):
        if self.allow_missing_data:
            self.writer.writerow([row.get(f,'').encode("utf-8") for n, f in enumerate(self.fieldnames)])
        else:
            self.writer.writerow([row[f].encode("utf-8") for n, f in enumerate(self.fieldnames)])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        self.writerow(self.fieldnames)
        for row in rows:
            self.writerow(row)

def dictwriter(data, keys):
    fieldnames = ['change']
    fieldnames.extend(keys)
    fieldnames = tuple(fieldnames)
    f = StringIO()
    writer = UnicodeDictWriter(f, fieldnames=fieldnames, allow_missing_data=True)
    headers = {}
    for n in fieldnames:
        headers[n] = n
    writer.writerow(headers)
    for d in data:
        row = {}
        for k in keys:
            row[k] = d.get(k,'')
        writer.writerow(row)

    
    return f.getvalue()

def listwriter(data):
    f = StringIO()
    writer = UnicodeWriter(f)
    writer.writerows(data)
    return f.getvalue()

class PhotoCSVResource(base.BasePage):

    @resource.GET()
    def GET(self, request):
        return self._html(request)

    @resource.POST()
    def POST(self, request):
        form = self._csvuploadform(request)
        try:
            data = form.validate(request)
        except formish.FormError:
            return self._html(request, form=form)
        f = StringIO()
        f.write(data['csv'].file.read())
        f.seek(0)

        rows = []
        try:
            reader = UnicodeDictReader(f)
            for row in reader:
                rows.append(row)
        finally:
            f.close()

        C = request.environ['couchish']
        with C.session() as S:
            photos = list(S.docs_by_view('photo/all'))
            photos_by_code = {}
            for photo in photos:
                photos_by_code[photo['code']] = photo
            changes = {}
            for row in rows:
                if row['change'] == 'y':
                    for key in CSVPHOTOKEYS:
                        if str(photos_by_code[row['code']][key]) != str(row[key]):
                            print 'setting',photos_by_code[row['code']]['code'],'key',key,'from',photos_by_code[row['code']][key],'to',row[key]
                            photos_by_code[row['code']][key] = row[key]

        flash.add_message(request.environ, 'csv uploaded.', 'success')
        return http.see_other(request.url)

    @templating.page('admin/csvupload.html')
    def _html(self, request, form=None):
        if not form:
            form = self._csvuploadform(request)
        return {'form': form}

    def _csvuploadform(self, request):
        schema = schemaish.Structure()
        schema.add('csv',schemaish.File())
        form = formish.Form(schema)
        form['csv'].widget = formish.FileUpload(CachedTempFilestore())
        return form

    @resource.child('csv')
    def csv(self, request, segments):
        return PhotoCSVDownloadResource()


class PhotoCSVDownloadResource(base.BasePage):


    @resource.GET(accept='text/csv')
    def GET(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            photos = list(S.view('photo/all',include_docs=True))
        photos = [p.doc for p in photos]
        photos.sort(key=itemgetter('ref'))
        out =  dictwriter(photos, CSVPHOTOKEYS)
        return http.ok([('Content-Type', 'text/csv')], out)


class ProductCSVResource(base.BasePage):

    @resource.GET()
    def GET(self, request):
        return self._html(request)

    @resource.POST()
    def POST(self, request):
        form = self._csvuploadform(request)
        try:
            data = form.validate(request)
        except formish.FormError:
            return self._html(request, form=form)

        replaceoptions = data['replaceoptions']
        deletemissing = data['deletemissing']
        updateall = data['updateall']
        f = StringIO()
        f.write(data['csv'].file.read())
        f.seek(0)

        changed_products = []
        try:
            reader = UnicodeReader(f)
            for row in reader:
                if row[0] == 'change':
                    continue

                if row[0] != '#':
                    product = dict([ (k, row[n]) for n,k in enumerate(CSVPRODUCTKEYS) ])
                    product['pricing'] = []
                    changed_products.append(product)
                else:
                    option = dict([ (k, row[n]) for n,k in enumerate(CSVOPTIONKEYS) ])
                    del option['marker']
                    product['pricing'].append(option)
        finally:
            f.close()

        C = request.environ['couchish']
        with C.session() as S:
            products = list(S.docs_by_view('product/all'))
            products_by_code = {}
            for product in products:
                products_by_code[product['code']] = product
            original = set(products_by_code.keys())
            new = set([p['code'] for p in changed_products])
            deleted = original.difference(new)
            changes = {}
            for product in changed_products:
                if product['change'] == 'y' or updateall:
                    if replaceoptions:
                        print 'code',product['code']
                        if products_by_code[product['code']]['pricing'] != product['pricing']:
                            print 'old options',products_by_code[product['code']]['pricing']
                            print 'new options',product['pricing']
                            print '==========='
                        products_by_code[product['code']]['pricing'] = product['pricing']
                    else:
                        for key in ['title','show','available','type']:
                            if str(products_by_code[product['code']].get(key,'')) != str(product.get(key,'')):
                                print 'setting',products_by_code[product['code']]['code'],'key',key,'from',products_by_code[product['code']][key],'to',product[key]
                                # CSVPRODUCTKEYS = ['change','code','title', 'show', 'available', 'type']
                                if key == 'show' or key == 'available':
                                    products_by_code[product['code']][key] = (product[key] == 'True')
                                    pass
                                else:
                                    products_by_code[product['code']][key] = product[key]
                                    pass
        with C.session() as S:
            if deletemissing:
                for d in deleted:
                    product = products_by_code[d]
                    doc = S.doc_by_id(product['_id'])
                    print 'deleteing',d
                    S.delete(doc)
                
                        



        flash.add_message(request.environ, 'csv uploaded.', 'success')
        return http.see_other(request.url)

    @templating.page('admin/csvupload.html')
    def _html(self, request, form=None):
        if not form:
            form = self._csvuploadform(request)
        return {'form': form}

    def _csvuploadform(self, request):
        schema = schemaish.Structure()
        schema.add('csv',schemaish.File())
        schema.add('replaceoptions',schemaish.Boolean(title='Replace Options'))
        schema.add('deletemissing',schemaish.Boolean(title='Delete Missing'))
        schema.add('updateall',schemaish.Boolean(title='Update All'))
        form = formish.Form(schema)
        form['csv'].widget = formish.FileUpload(CachedTempFilestore())
        form['replaceoptions'].widget = formish.Checkbox()
        form['deletemissing'].widget = formish.Checkbox()
        form['updateall'].widget = formish.Checkbox()
        return form

    @resource.child('csv')
    def csv(self, request, segments):
        return ProductCSVDownloadResource()

class ProductCSVDownloadResource(base.BasePage):

    @resource.GET(accept='text/csv')
    def GET(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            rows = list(S.view('product/all',include_docs=True))
        products = []
        options = {}
        for row in rows:
            product = row.doc
            options[product['code']] = list(product['pricing'])
            del product['pricing']
            del product['photo']
            if 'sizes' in product:
                del product['sizes']
            products.append(product)
        products.sort(key=itemgetter('code'))
        out = []
        out.append(CSVPRODUCTKEYS)
        for product in products:
            row = [product.get(k,'') for k in CSVPRODUCTKEYS]
            out.append(row)
            for option in options[product['code']]:
                row = [option.get(k,'#') for k in CSVOPTIONKEYS]
                out.append(row)
        return http.ok([('Content-Type', 'text/csv')], listwriter(out))


class UserCSVResource(base.BasePage):

    @resource.child('csv')
    def csv(self, request, segments):
        return UserCSVDownloadResource()


class UserCSVDownloadResource(base.BasePage):


    @resource.GET(accept='text/csv')
    def GET(self, request):
        C = request.environ['couchish']
        with C.session() as S:
            users = list(S.view('user/all',include_docs=True))
        users = [p.doc for p in users]
        users.sort(key=itemgetter('last_name'))
        out =  dictwriter(users, CSVUSERKEYS)
        return http.ok([('Content-Type', 'text/csv')], out)
