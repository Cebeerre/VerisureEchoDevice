#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, jsonify
from flask import abort, request
from flask import make_response
import requests
import xmltodict
from datetime import datetime
import time
import shelve
import config
import sys
import os
import redis
from rq import Queue
from apiclient import VerisureAPIClient

# https://github.com/Cebeerre/VerisureEchoDevice
# Flask App to use with fauxmo (https://pypi.org/project/fauxmo/) to emulate the Verisure EU alarm as a WEMO (Belkin) bulb/plug.
# Cebeerre/VerisureEchoDevice is licensed under the MIT License
# https://pythonise.com/series/learning-flask/flask-rq-task-queue
# https://github.com/rq/rq/issues/582

ALARM_MODES = { 'peri': '40', 'armnight': '46', 'arm': '31'}
shelve_file=os.path.dirname(os.path.realpath(sys.argv[0]))+'/verisure_shelf'
app = Flask(__name__)
r = redis.Redis()
q = Queue(connection=r)

def set_alarm_status(action):
    s = shelve.open(shelve_file, writeback=True)
    if action == 'darm':
        s[ALARM_MODES['peri']] = '0'
        s[ALARM_MODES['armnight']] = '0'
        s[ALARM_MODES['arm']] = '0'
    else:
        s[ALARM_MODES[action]] = ALARM_MODES[action]
    s.close()

def return_alarm_status(action):
    s = shelve.open(shelve_file, flag='r')
    if action in s:
        status = {}
        status["status"] = s[action]
        output = jsonify(status)
        s.close()
        return output
    else:
        abort(404)

def synclog():
    s = shelve.open(shelve_file, writeback=True)
    status = VerisureAPIClient('log',config.USER,config.PWD,config.NUMINST,config.PANEL, config.COUNTRY, config.LANG, config.SECONDS_BETWEEN_REQUESTS)
    regs = status['PET']['LIST']['REG']
    dect = False
    for reg in regs:
        if reg['@type'] == '32':
            if dect:
                pass
            else:
                s[ALARM_MODES['peri']] = '0'
                s[ALARM_MODES['armnight']] = '0'
                s[ALARM_MODES['arm']] = '0'
            break
        elif reg['@type'] in ALARM_MODES.values():
            s[reg['@type']] = reg['@type']
            dect = True
    s.close()

@app.route('/api/v1.0/<alarm_action>', methods=['GET'])
def operate_alarm(alarm_action):
    if len(alarm_action) == 0:
        abort(404)
    if alarm_action == 'peri':
        q.enqueue(VerisureAPIClient,args=(alarm_action,config.USER,config.PWD,config.NUMINST,config.PANEL, config.COUNTRY, config.LANG, config.SECONDS_BETWEEN_REQUESTS))
        set_alarm_status(alarm_action)
        output = jsonify(success=True)
    elif alarm_action == 'darm':
        q.enqueue(VerisureAPIClient,args=(alarm_action,config.USER,config.PWD,config.NUMINST,config.PANEL, config.COUNTRY, config.LANG, config.SECONDS_BETWEEN_REQUESTS))
        set_alarm_status(alarm_action)
        output = jsonify(success=True)
    elif alarm_action == 'armnight':
        q.enqueue(VerisureAPIClient,args=(alarm_action,config.USER,config.PWD,config.NUMINST,config.PANEL, config.COUNTRY, config.LANG, config.SECONDS_BETWEEN_REQUESTS))
        set_alarm_status(alarm_action)
        output = jsonify(success=True)
    elif alarm_action == 'arm':
        q.enqueue(VerisureAPIClient,args=(alarm_action,config.USER,config.PWD,config.NUMINST,config.PANEL, config.COUNTRY, config.LANG, config.SECONDS_BETWEEN_REQUESTS))
        set_alarm_status(alarm_action)
        output = jsonify(success=True)
    elif alarm_action == 'status':
        alarm = request.args.get('alarm')
        if alarm:
            output = return_alarm_status(alarm)
        else:
            abort(404)
    elif alarm_action == 'synclog':
        synclog()
        output = jsonify(success=True)
    else:
        abort(404)
    return output

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=False,threaded=True,host='127.0.0.1',port='5000')
