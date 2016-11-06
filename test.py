#!/usr/bin/env python
# encoding: utf-8

'''
Created on Nov 6, 2016

@author: Yusuke Kawatsu
'''

# built-in modules.
import os
import json

# installed modules.
import psutil

# my modules.
from healthcheckapi import app, _load_config, _update_onmemory_config, _Dot
from healthcheckapi import _check_process, _get_proccesses, _check_http


######## TESTS ########

def test__check_process():
    proc_list = [
        { u'pid': 5555, u'name': u'Target1', u'cmdline': [ u'/bin/target1' ], u'status': u'running' },
        { u'pid': 6666, u'name': u'Target2', u'cmdline': [ u'/bin/target2', '-h' ], u'status': u'running' },
        { u'pid': 111, u'name': u'dummy1', u'cmdline': [ u'/bin/dummy1' ], u'status': u'running' },
        { u'pid': 222, u'name': u'dummy2', u'cmdline': [ u'/bin/dummy2', '-x' ], u'status': u'running' }
    ]
    
    # pid.
    assert not _check_process(_create_config(target_process=[ { u'pid': 5555 } ]), proc_list)
    assert not _check_process(_create_config(target_process=[ { u'pid': 6666 } ]), proc_list)
    assert _check_process(_create_config(target_process=[ { u'pid': 444 } ]), proc_list)
    
    # name.
    assert not _check_process(_create_config(target_process=[ { u'name': u'Target1' } ]), proc_list)
    assert not _check_process(_create_config(target_process=[ { u'name': u'Target2' } ]), proc_list)
    assert _check_process(_create_config(target_process=[ { u'name': u'NO_MATCH_NAME' } ]), proc_list)
    
    # matching.
    assert not _check_process(_create_config(target_process=[ { u'matching': u'/bin/target1' } ]), proc_list)
    assert not _check_process(_create_config(target_process=[ { u'matching': u'^/bin/target1$' } ]), proc_list)
    assert not _check_process(_create_config(target_process=[ { u'matching': u'^.*target1.*$' } ]), proc_list)
    assert not _check_process(_create_config(target_process=[ { u'matching': u'/bin/target2 -h' } ]), proc_list)
    assert not _check_process(_create_config(target_process=[ { u'matching': u'^/bin/target2[ ]+-h$' } ]), proc_list)
    assert not _check_process(_create_config(target_process=[ { u'matching': u'^.*target2[ ]+.*$' } ]), proc_list)
    assert _check_process(_create_config(target_process=[ { u'matching': u'target1' } ]), proc_list)
    assert _check_process(_create_config(target_process=[ { u'matching': u'Target1' } ]), proc_list)
    assert _check_process(_create_config(target_process=[ { u'matching': u'/bin/target-h' } ]), proc_list)
    assert _check_process(_create_config(target_process=[ { u'matching': u' /bin/target -h ' } ]), proc_list)

def test__check_http():
    # "url": "https://localhost/foo/bar"
    assert not _check_http(_create_config(target_http=[ { u'url': u'http://google.com' } ]))
    assert not _check_http(_create_config(target_http=[ { u'url': u'https://google.com' } ]))
    assert not _check_http(_create_config(target_http=[ { u'url': u'https://www.python.org/about/' } ]))
    assert _check_http(_create_config(target_http=[ { u'url': u'http://foo.bar.com/baz/' } ]))
    
    # :todo: think proxy...
    
    # "healthy_status_codes": [ 200, 201 ]
    assert not _check_http(_create_config(target_http=[ { u'url': u'http://google.com', u'healthy_status_codes': [ 200 ] } ]))
    assert not _check_http(_create_config(target_http=[ { u'url': u'http://google.com', u'healthy_status_codes': [ 200, 201, 202, 203 ] } ]))
    assert _check_http(_create_config(target_http=[ { u'url': u'http://google.com', u'healthy_status_codes': [ 400, 500 ] } ]))
    
    # "verify": true/false
    assert not _check_http(_create_config(target_http=[ { u'url': u'https://expired.badssl.com/', u'verify': False } ]))
    assert _check_http(_create_config(target_http=[ { u'url': u'https://expired.badssl.com/', u'verify': True } ]))
    assert _check_http(_create_config(target_http=[ { u'url': u'https://expired.badssl.com/' } ]))
    
    assert not _check_http(_create_config(target_http=[ { u'url': u'https://self-signed.badssl.com/', u'verify': False } ]))
    assert _check_http(_create_config(target_http=[ { u'url': u'https://self-signed.badssl.com/', u'verify': True } ]))
    assert _check_http(_create_config(target_http=[ { u'url': u'https://self-signed.badssl.com/' } ]))

def test__get_proccesses():
    proc_list = _get_proccesses()
    
    # a proc has "pid", "name", "cmdline", "status".
    assert len(proc_list) > 0
    assert reduce(lambda pre, proc: pre and isinstance(proc[u'pid'], int), proc_list, True)
    assert reduce(lambda pre, proc: pre and isinstance(proc[u'name'], unicode), proc_list, True)
    assert reduce(lambda pre, proc: pre and isinstance(proc[u'cmdline'], list), proc_list, True)
    assert reduce(lambda pre, proc: pre and isinstance(proc[u'status'], unicode), proc_list, True)

######## FLASK TESTS ########

def test_healthcheck_api():
    client = app.test_client()
    
    # process: name.
    _update_onmemory_config(_create_config(target_process=[ { u'name': u'Python' } ]))
    assert client.get(u'/').status_code == 200
    
    _update_onmemory_config(_create_config(target_process=[ { u'name': u'NO_MATCH_NAME' } ]))
    assert client.get(u'/').status_code == 500
    
    # process: matching.
    _update_onmemory_config(_create_config(target_process=[ { u'matching': u'^.*nosetests.*$' } ]))
    assert client.get(u'/').status_code == 200
    
    _update_onmemory_config(_create_config(target_process=[ { u'matching': u'nosetests' } ]))
    assert client.get(u'/').status_code == 500
    
    # http: matching.
    _update_onmemory_config(_create_config(target_http=[ { u'url': u'http://google.com' } ]))
    assert client.get(u'/').status_code == 200
    
    _update_onmemory_config(_create_config(target_http=[ { u'url': u'http://foo.bar.com/baz' } ]))
    assert client.get(u'/').status_code == 500
    
    # status code settings.
    _update_onmemory_config(_create_config(status_code_healthy=201, status_code_unhealthy=501, target_process=[ { u'name': u'Python' } ]))
    assert client.get(u'/').status_code == 201
    
    _update_onmemory_config(_create_config(status_code_healthy=201, status_code_unhealthy=501, target_process=[ { u'name': u'NO_MATCH_NAME' } ]))
    assert client.get(u'/').status_code == 501
    
    # :todo: url.

######## UTIL FUNCTIONS ########

def _create_config(**kwargs):
    '''
    :rtype: :class:`_Dot`
    '''
    base_conf = {
      u'url': u'/',
      u'port': 5000,
      u'status_code_healthy': 200,
      u'status_code_unhealthy': 500,
      u'target_process': [],
      u'target_http': []
    }
    
    return _Dot(dict(base_conf, **kwargs))


if __name__ == '__main__':
    test__get_proccesses()
