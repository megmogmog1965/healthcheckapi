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
from flask import Flask
from flask import jsonify
from flask.helpers import make_response

# my modules.
pass


# flask app.
app = Flask(__name__, static_path=u'/static', static_folder=u'./static')
app.debug = True


# config default.
_config_deafult = ur'''{
  "url": "/",
  "port": 5000,
  "status_code_healthy": 200,
  "status_code_unhealthy": 500,
  
  "target_process": [
    {
      "pid": 3376,
      "name": "Python",
      "matching": "^.+/python .+$"
    }
  ],
  
  "target_http": [
    {
      "url": "https://foo.bar.com:80/baz",
      "healthy_status_codes": [ 200, 201 ]
    }
  ]
}
'''


######## UTIL CLASSES ########

class _Dot(object):
    def __init__(self, inner):
        self._inner = inner
    
    def __getattr__(self, attr):
        raw = self._inner[attr]
        return _Dot(raw) if isinstance(raw, (dict, list, tuple, )) else raw
    
    def __iter__(self):
        for raw in self._inner:
            yield _Dot(raw) if isinstance(raw, (dict, list, tuple, )) else raw

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
    
    # create default if not exists.
    if not os.path.isfile(config_path):
        with codecs.open(config_path, 'w', 'utf-8') as f:
            f.write(_config_deafult)
    
    # load config.
    with codecs.open(config_path, 'r', 'utf-8') as f:
        obj = json.load(f)
    
    __cached_conf = _Dot(obj)
    return __cached_conf
__cached_conf = None

######## BUSINESS LOGIC FUNCTIONS ########

def _check_process(config, process_list):
    def eval_condi(condi, process_list):
        procs = [ _Dot(p) for p in process_list ]
        res = False
        
        # pid.
        res = res or reduce(lambda pre, proc: pre or proc.pid == condi.pid, procs, False)
        
        # name.
        res = res or reduce(lambda pre, proc: pre or proc.name == condi.name, procs, False)
        
        # matching.
        res = res or reduce(lambda pre, proc: pre or re.match(condi.matching, u' '.join(proc.cmdline)), procs, False)
        
        return bool(res)
    
    conditions = config.target_process
    is_healthy = reduce(lambda pre, cond: pre and eval_condi(cond, process_list), conditions, True)
    
    return is_healthy

def _check_http(config):
    # :todo: implement me.
    return True

def _get_current_proccesses():
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
    process_list = _get_current_proccesses()
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
    is_healthy = True
    
    # check process.
    is_healthy = is_healthy and _check_process(config, _get_current_proccesses())
    
    # check http.
    is_healthy = is_healthy and _check_http(config)
    
    return make_response(u'Healthy', config.status_code_healthy) if is_healthy else make_response(u'Unhealthy', config.status_code_unhealthy)


if __name__ == '__main__':
    # print current processes.
    config = _load_config()
    print u'current processes:'
    print _print_format_processes()
    
    # run web server.
    # :see: http://askubuntu.com/questions/224392/how-to-allow-remote-connections-to-flask
    app.run(host='0.0.0.0', port=config.port, threaded=True, use_reloader=False)
