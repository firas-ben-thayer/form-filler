# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

bind = '0.0.0.0:5000'
workers = 3
worker_class = 'gevent'
accesslog = '-'
errorlog = '-'  # Logs to stderr
loglevel = 'debug'
capture_output = True
enable_stdio_inheritance = True
