import copy

from repoxplorer.controllers.renderers import CSVRenderer

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
            'level': 'INFO',
            'formatter': 'normal',
            'filename': '',
            'when': 'D',
            'interval': 1,
            'backupCount': 30,
        },
    },
    'formatters': {
        'console': {'format': ('%(levelname)-5.5s [%(name)s]'
                    '[%(threadName)s] %(message)s')},
        'normal': {'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                   '[%(threadName)s] %(message)s')},
    }
}

# Pecan REST and rendering configuration
app = {
    'root': 'repoxplorer.controllers.root.RootController',
    'modules': ['repoxplorer'],
    'custom_renderers': {'csv': CSVRenderer},
    'static_root': '/usr/share/repoxplorer/public',
    'template_path': '/usr/share/repoxplorer/templates',
    'debug': False,
    'errors': {
        404: '/error/e404',
        '__force_dict__': True
    }
}

# Additional RepoXplorer configurations
db_default_file = None
db_path = '/etc/repoxplorer/'
git_store = '/var/lib/repoxplorer/git_store'
xorkey = None
elasticsearch_host = 'localhost'
elasticsearch_port = 9200
elasticsearch_index = 'repoxplorer'
indexer_loop_delay = 60
index_custom_html = ""
users_endpoint = False
admin_token = 'admin_token'

# Logging configuration for the wsgi app
logging = copy.deepcopy(base_logging)
logging['handlers']['normal']['filename'] = (
    '/var/log/repoxplorer/repoxplorer-webui.log')

# Logging configuration for the indexer
indexer_logging = copy.deepcopy(base_logging)
indexer_logging['handlers']['normal']['filename'] = (
    '/var/log/repoxplorer/repoxplorer-indexer.log')
