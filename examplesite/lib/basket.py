from __future__ import with_statement
from itertools import chain, repeat, izip

from restish import resource, http, templating
from wsgiapptools import cookies
from couchish import errors

from commerce import basket as c_basket

from examplesite import who


import logging

log = logging.getLogger(__name__)


    

class Basket(c_basket.Basket):

    def __init__(self, request):
        self._items = []
        self.request = request
        self.C = self.request.environ['couchish']
        self.basket_id = self.request.cookies.get('basket_id')

    def load(self):
        if self.basket_id is not None:
            with self.C.session() as S:
                try:
                    basket_data = S.doc_by_id(self.basket_id)
                except errors.NotFound, e:
                    self.basket_id = None
                    return
                items = S.docs_by_id([i['_id'] for i in basket_data['items']])
            items_dict = dict([(item['_id'],item) for item in items])
            for item in basket_data['items']:

                self.add(BasketItem(items_dict[item['_id']]), item['option'], item['quantity'])

    def save(self):
        items = []
        for item in self._items:
            items.append( {'_id': item.item.original['_id'], 'item': item.item.original, 'option': item.option, 'quantity': item.quantity} )
        if self.basket_id is None:
            with self.C.session() as S:
                basket_data = {'model_type': 'basket', 'items': items}
                basket_id = S.create(basket_data)
            cookies.set_cookie(self.request.environ, ('basket_id', basket_id) )
        else:
            with self.C.session() as S:
                old_basket_data = S.doc_by_id(self.basket_id)
                old_basket_data['items'] = items

class BasketItem(object):
    filter_attrs = ['_id','code','title','information','pricing','type']

    def __init__(self, original):
        self.id = original['_id']
        self.original = self.filter(original)
        self.code = original['code']
        self.options = self.original['pricing']

    def description(self, option_id):
        option = [o for o in self.options if o['option'] == option_id][0]
        label = option.get('label' ,option['option']).title()
        return '%s\n%s'%(self.original['title'],label)

    def get_price(self, option_id):
        option = [o for o in self.options if o['option'] == option_id][0]
        return option['price']

    def get_postage(self, option_id):
        option = [o for o in self.options if o['option'] == option_id][0]
        return option['postage']

    def filter(self, original):
        filtered = {}
        for attr in self.filter_attrs:
            filtered[attr] = original[attr]
        filtered['ref'] = original['photo']['ref']
        filtered['photo'] = {'id': original['photo']['photo']['id'],'doc_id': original['photo']['_ref'], 'metadata': original['photo']['photo']['metadata']}

        #if original['type'] == 'Print' or original['type'] == 'Canvas':
            #filtered['pricing'] = pricing.get_options(original)
        #else:
            #filtered['pricing'] = original['pricing']
        filtered['pricing'] = original['pricing']
        return filtered
            

    def __repr__(self):
        return '<CouchishBasketItem id="%s", code="%s", options="%r">'%(self.id, self.code, self.options)



