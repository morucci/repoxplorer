import os
import sys
import copy

from repoxplorer.controllers.renderers import CSVRenderer

runtimedir = os.path.join(os.path.expanduser('~'), '.local', 'repoxplorer')

# RepoXplorer configuration file
base_logging = {
    'version': 1,
    'root': {'level': 'DEBUG', 'handlers': ['normal']},
    'loggers': {
        'indexerDaemon': {
            'level': 'DEBUG',
            'handlers': ['normal', 'console'],
            'propagate': False,
        },
        'repoxplorer': {
            'level': 'DEBUG',
            'handlers': ['normal', 'console'],
            'propagate': False,
        },
        'elasticsearch': {
            'level': 'WARN',
            'handlers': ['normal', 'console'],
            'propagate': False,
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'normal': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'normal',
            'filename': '',
            'when': 'D',
            'interval': 1,
            'backupCount': 30,
        },
    },
    'formatters': {
        'console': {'format': ('%(levelname)-5.5s [%(name)s] %(message)s')},
        'normal': {'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                              ' %(message)s')},
    }
}

# Internal dev pecan server
server = {
    'port': '51000',
    'host': '0.0.0.0'
}

# Pecan REST and rendering configuration
app = {
    'root': 'repoxplorer.controllers.root.RootController',
    'modules': ['repoxplorer'],
    'custom_renderers': {'csv': CSVRenderer},
    'static_root': '%s/public' % runtimedir,
    'debug': False,
    'errors': {
        404: '/error/e404',
        '__force_dict__': True
    }
}

# Additional RepoXplorer configurations
db_default_file = None
db_path = runtimedir
db_cache_path = db_path
git_store = '%s/git_store' % runtimedir
xorkey = None
elasticsearch_host = 'localhost'
elasticsearch_port = 9200
elasticsearch_index = 'repoxplorer'
indexer_loop_delay = 60
indexer_skip_projects = []
index_custom_html = ""
users_endpoint = False
admin_token = 'admin_token'

# Logging configuration for the wsgi app
logging = copy.deepcopy(base_logging)
logging['handlers']['normal']['filename'] = (
    '%s/repoxplorer-api.log' % runtimedir)

# Logging configuration for the indexer
indexer_logging = copy.deepcopy(base_logging)
indexer_logging['handlers']['normal']['filename'] = (
    '%s/repoxplorer-indexer.log' % runtimedir)
