server = {
    'port': '8080',
    'host': 'localhost'
}

app = {
    'root': 'repoxplorer.controllers.root.RootController',
    'modules': ['repoxplorer'],
    'debug': True,
}

logging = {
    'loggers': {
        'repoxplorer': {'level': 'DEBUG', 'handlers': ['console']},
    },
    #'root': {'level': 'INFO', 'handlers': ['console']},
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        },
    }
}
