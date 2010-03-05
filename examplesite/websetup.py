"""
PasteDeploy setup-app support for the examplesite application.
"""

import logging
from paste.deploy import appconfig

import adminish, couchish, couchdb
import couchish

log = logging.getLogger(__name__)


def setup_config(command, filename, section, vars):
    """
    Place any commands to setup the initial state of your application here.
    """
    # Load the application's config.
    conf = appconfig('config:'+filename, section.split(':',1)[1])

    log.info("setup_config is not configured. (see %s)" % __file__)


def setup_app(command, app_conf, vars):
    couchish_config = adminish.config.make_couchish_config(app_conf, 'examplesite.model')
    db = couchdb.Database(app_conf['couchish.db.url'])
    store = couchish.CouchishStore(db, couchish_config)
    #adminish_config = adminish.config.add_initial_data(couchish_config, store)
    store.sync_views()


