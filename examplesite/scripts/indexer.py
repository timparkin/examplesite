"""
Simple script to index a database using the joecornish.lib.index module.
"""

import logging
import sys
import couchdb

import adminish, couchish
from adminish import index


def main(db_url, model_module, cache_dir):
    couchish_config = adminish.config.make_couchish_config(None, model_module)
    _db = couchdb.Database(db_url)
    db = couchish.CouchishStore(_db, couchish_config)
    adminish_config = adminish.config.make_adminish_config(couchish_config, store_factory=lambda request: db)
    indexer = index.Indexer(_db, cache_dir, adminish_config=adminish_config, forever=True)
    indexer()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db_url = sys.argv[1]
    model_module = sys.argv[2]
    cache_dir = sys.argv[3]
    main(db_url, model_module, cache_dir)

