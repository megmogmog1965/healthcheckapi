#!/usr/bin/env python
# encoding: utf-8

'''
Created on Nov 7, 2016

@author: Yusuke Kawatsu
'''

# built-in modules.
import os

# installed modules.
import win32serviceutil

# my modules.
from healthcheckapi import run, stop


class SampleService(win32serviceutil.ServiceFramework):
    
    _svc_name_ = 'healthcheckapi'
    _svc_display_name_ = 'healthcheckapi'
    _svc_description_ = 'The python script service that provides health check api.'
    
    def SvcDoRun(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__))) # for file-handler logging.
        run()
    
    def SvcStop(self):
        stop()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SampleService)
