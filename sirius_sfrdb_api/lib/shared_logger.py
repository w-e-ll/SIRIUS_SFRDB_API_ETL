#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os
import sys


def is_interactive_shell():
    """
    If environment-variable $TERM is present, we are running this code in a interactive shell
    Else we are from cron or we called via nrpe as a nagios-check.
    :return: boolean
    """
    return True if os.environ.get('TERM', None) else False


def setup_logger(logfile=None, stdout=False, level=logging.INFO, max_bytes=1024*1024*10, backup_count=10):
    """
    Initialize the root logger (give it the name: '.'):
    * If logfile is provided: log to a rotating file
    * If stdout is true: log to screen as well; if TERM env var exists, then stdout is set to True by default
    * If logfile not provided: log to screen only (regardless of stdout)
    """
    root = logging.getLogger()
    root.name = '.'

    formatter = logging.Formatter('%(asctime)s %(process)5d %(levelname)-5s %(message)s')
    logging.addLevelName(logging.WARN, 'WARN')  # WARNING is such a long word...
    logging.addLevelName(logging.CRITICAL, 'FATAL')

    hdlr_stdout = logging.StreamHandler(sys.stdout)
    hdlr_stdout.setFormatter(formatter)

    if is_interactive_shell():
        stdout = True

    if logfile is None:
        # Log to screen only
        root.addHandler(hdlr_stdout)
    else:
        # Log to file
        if not os.path.isdir(os.path.dirname(logfile)):
            os.makedirs(os.path.dirname(logfile))
        hdlr_file = logging.handlers.RotatingFileHandler(logfile, 'a', max_bytes, backup_count)
        hdlr_file.setFormatter(formatter)
        root.addHandler(hdlr_file)
        if stdout:
            root.addHandler(hdlr_stdout)
    root.setLevel(level)
    return root