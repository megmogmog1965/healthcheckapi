#!/usr/bin/env python
# encoding: utf-8

'''
Created on Nov 5, 2016

@author: Yusuke Kawatsu
'''

# built-in modules.
import os
import re
import json
import codecs
import logging
from logging.config import fileConfig

# installed modules.
import psutil
import requests
from flask import Flask
from flask import jsonify
from flask import request
from flask.helpers import make_response

# my modules.
pass


######## GLOBALS ########

# flask app.
app = Flask(__name__, static_path=u'/static', static_folder=u'./static')
app.debug = True

######## UTIL CLASSES ########

class _Dot(object):
    def __init__(self, inner):
        self._inner = inner
    
    def __getattr__(self, attr):
        raw = self._inner[attr]
        return _Dot(raw) if isinstance(raw, (dict, list, tuple, )) else raw
    
    def __contains__(self, item):
        return item in self._inner
    
    def __iter__(self):
        for raw in self._inner:
            yield _Dot(raw) if isinstance(raw, (dict, list, tuple, )) else raw
    
    def get_raw(self):
        return self._inner

######## UTIL FUNCTIONS ########

def _root_dir():
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    return _to_unicode(parent_dir)

def _to_unicode(encodedStr):
    if isinstance(encodedStr, unicode):
        return encodedStr
    for charset in [ u'utf-8', u'cp932', u'euc-jp', u'shift-jis', u'iso2022-jp' ]:
        try: return encodedStr.decode(charset)
        except: pass

def _logger():
    global __cached_logger
    if __cached_logger:
        return __cached_logger
    
    _conf_path = os.path.join(_root_dir(), u'logging.ini')
    fileConfig(_conf_path)
    __cached_logger = logging.getLogger(u'healthcheckapi')
    return __cached_logger
__cached_logger = None

def _ignore_exception(fn, default=None):
    '''
    :rtype: function
    '''
    def safe(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except:
            return default
    return safe

def _load_config():
    '''
    :rtype: :class:`_Dot`
    '''
    global __cached_conf
    config_path = os.path.join(_root_dir(), u'config.json')
    
    # if cached.
    if __cached_conf:
        return __cached_conf
    
    # load config.
    with codecs.open(config_path, 'r', 'utf-8') as f:
        obj = json.load(f)
    
    __cached_conf = _Dot(obj)
    return __cached_conf
__cached_conf = None

######## BUSINESS LOGIC FUNCTIONS ########

def _check_process(config, process_list):
    '''
    :param _Dot config: config root.
    :param list process_list: see :function:`_get_proccesses`
    :rtype: list of :class:`_Dot`
    :return: a list of error conditions.
    '''
    def eval_condition(condition, process_list):
        procs = [ _Dot(p) for p in process_list ]
        res = False
        
        # pid.
        res = res or reduce(lambda pre, proc: pre or proc.pid == condition.pid, procs, False)
        
        # name.
        res = res or reduce(lambda pre, proc: pre or proc.name == condition.name, procs, False)
        
        # matching.
        res = res or reduce(lambda pre, proc: pre or re.match(condition.matching, u' '.join(proc.cmdline)), procs, False)
        
        return bool(res)
    
    conditions = config.target_process
    errors = map(lambda cond: None if eval_condition(cond, process_list) else cond, conditions)
    errors = filter(lambda cond: cond, errors)
    
    return errors

def _check_http(config):
    '''
    :param _Dot config: config root.
    :rtype: list of :class:`_Dot`
    :return: a list of error conditions.
    '''
    def eval_condition(condition):
        # :todo: http, https, no-protocol.
        url = condition.url
        
        try:
            if url.startswith(u'http://'):
                res = requests.get(url)
            elif url.startswith(u'https://'):
                res = requests.get(url, verify=condition.verify if 'verify' in condition else True)
            else:
                res = requests.get(u'http://127.0.0.1:80/%s' % (url.lstrip(u'/')))
        except:
            return False
        
        return res.status_code in condition.healthy_status_codes if condition.healthy_status_codes else res.status_code == 200
    
    conditions = config.target_http
    errors = map(lambda cond: None if eval_condition(cond) else cond, conditions)
    errors = filter(lambda cond: cond, errors)
    
    return errors

def _get_proccesses():
    '''
    :rtype: list of dict
    :return: [ { 'pid': int, 'name': unicode, 'cmdline': list, 'status': unicode }, ... ]
    '''
    def format_proc(proc):
        return {
            u'pid': proc.pid,
            u'name': _to_unicode(proc.name()),
            u'cmdline': [ _to_unicode(p) for p in proc.cmdline() ],
            u'status': _to_unicode(proc.status())
        }
    
    process_list = psutil.process_iter()
    process_list = map(_ignore_exception(format_proc), process_list)
    process_list = filter(lambda ps: ps, process_list)
    
    return process_list

def _print_format_processes():
    '''
    :rtype: unicode
    '''
    process_list = _get_proccesses()
    process_list = map(lambda ps: dict(ps, cmdline=u' '.join(ps[u'cmdline'])), process_list)
    
    msg = json.dumps(process_list, indent=2)
    return msg

######## FLASK API DEFS ########

@app.route(_load_config().url, methods=['GET'])
def healthcheck_api():
    '''
    HTTP GET API to provide health check result.
    '''
    config = _load_config()
    errors = []
    
    print request.url
    
    # check process.
    errors = errors + _check_process(config, _get_proccesses())
    
    # check http.
    errors = errors + _check_http(config)
    
    # to native objects from _Dot.
    errors = map(lambda e: e.get_raw(), errors)
    
    if errors:
        return make_response(jsonify(errors=errors), config.status_code_unhealthy)
    
    return make_response(jsonify({}), config.status_code_healthy)


if __name__ == '__main__':
    # print current processes.
    config = _load_config()
    print u'current processes:'
    print _print_format_processes()
    
    # run web server.
    # :see: http://askubuntu.com/questions/224392/how-to-allow-remote-connections-to-flask
    app.run(host='0.0.0.0', port=config.port, threaded=True, use_reloader=False)