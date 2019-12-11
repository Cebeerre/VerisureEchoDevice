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
from flask_executor import Executor

# https://github.com/Cebeerre/VerisureEchoDevice
# Flask App to use with fauxmo (https://pypi.org/project/fauxmo/) to emulate the Verisure EU alarm as a WEMO (Belkin) bulb/plug.
# Cebeerre/VerisureEchoDevice is licensed under the MIT License

USER = config.USER
PWD = config.PWD
NUMINST = config.NUMINST
PANEL = config.PANEL
COUNTRY = config.COUNTRY
LANG = config.LANG
SECONDS_BETWEEN_REQUESTS = config.SECONDS_BETWEEN_REQUESTS
LOGIN_PAYLOAD = { 'Country': COUNTRY, 'user':USER, 'pwd': PWD, 'lang': LANG }
OP_PAYLOAD = { 'Country': COUNTRY, 'user':USER, 'pwd': PWD, 'lang': LANG, 'panel': PANEL, 'numinst': NUMINST}
OUT_PAYLOAD = { 'Country': COUNTRY, 'user':USER, 'pwd': PWD, 'lang': LANG, 'numinst': '(null)'}
ALARM_MODES = { 'armoutside': '40', 'armnight': '46', 'arm': '31'}
shelve_file=os.path.dirname(os.path.realpath(sys.argv[0]))+'/verisure_shelf'
BASE_URL='https://mob2217.securitasdirect.es:12010/WebService/ws.do'
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
app = Flask(__name__)
executor = Executor(app)

@app.route('/api/v1.0/<alarm_action>', methods=['GET'])
def operate_alarm(alarm_action):
    if len(alarm_action) == 0:
        abort(404)
    if alarm_action == 'armoutside':
        executor.submit(arm_outside)
        set_alarm_status(alarm_action)
        output = jsonify(success=True)
    elif alarm_action == 'disarm':
        executor.submit(disarm_all)
        set_alarm_status(alarm_action)
        output = jsonify(success=True)
    elif alarm_action == 'armnight':
        executor.submit(arm_night)
        set_alarm_status(alarm_action)
        output = jsonify(success=True)
    elif alarm_action == 'arm':
        executor.submit(arm_total_inside)
        set_alarm_status(alarm_action)
        output = jsonify(success=True)
    elif alarm_action == 'status':
        alarm = request.args.get('alarm')
        if alarm:
            output = return_alarm_status(alarm)
        else:
            abort(404)
    elif alarm_action == 'synclog':
        output = synclog()
        #output = jsonify(success=True)
    else:
        abort(404)
    return output

def set_alarm_status(action):
    s = shelve.open(shelve_file, writeback=True)
    if action == 'disarm':
        s[ALARM_MODES['armoutside']] = '0'
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

def call_verisure_get(method, parameters):
    time.sleep(SECONDS_BETWEEN_REQUESTS)
    if method == 'GET':
        response = requests.get(BASE_URL, params=parameters)
    elif method == 'POST':
        response = requests.post(BASE_URL, params=parameters)
    if response.status_code == 200:
        output = xmltodict.parse(response.text)
        return output
    else:
        return None

def op_verisure(action,hash,id):
    payload = OP_PAYLOAD
    payload.update({'request': action+'1', 'hash': hash, 'ID': id})
    call_verisure_get('GET',payload)
    payload['request'] = action+'2'
    output = call_verisure_get('GET',payload)
    res = output['PET']['RES']
    while res != 'OK':
        output = call_verisure_get('GET',payload)
        res = output['PET']['RES']
    status = output['PET']['STATUS']
    msg = output['PET']['MSG']
    return { 'result': res, 'status': status, 'message': msg }

def generate_id():
    ID='IPH_________________________'+USER+datetime.now().strftime("%Y%m%d%H%M%S")
    return ID

def get_login_hash():
    payload = LOGIN_PAYLOAD
    payload.update({'request': 'LOGIN', 'ID': generate_id()})
    output = call_verisure_get('POST',payload)
    return output['PET']['HASH']

def logout(hash):
    payload = OUT_PAYLOAD
    payload.update({'request': 'CLS', 'hash': hash, 'ID': generate_id()})
    output = call_verisure_get('GET', payload)
    return output

def arm_outside():
    hash = get_login_hash()
    id = generate_id()
    status = op_verisure('PERI', hash, id)
    logout(hash)
    return jsonify(status)

def arm_total_inside():
    hash = get_login_hash()
    id = generate_id()
    status = op_verisure('ARM', hash, id)
    logout(hash)
    return jsonify(status)

def disarm_all():
    hash = get_login_hash()
    id = generate_id()
    status = op_verisure('DARM', hash, id)
    logout(hash)
    return jsonify(status)

def arm_night():
    hash = get_login_hash()
    id = generate_id()
    status = op_verisure('ARMNIGHT', hash, id)
    logout(hash)
    return jsonify(status)

def synclog():
    s = shelve.open(shelve_file, writeback=True)
    hash = get_login_hash()
    id = generate_id()
    payload = OP_PAYLOAD
    payload.update({'request': 'ACT_V2', 'hash':hash, 'ID':id, 'timefilter': '2', 'activityfilter': '0'})
    status = call_verisure_get('GET',payload)
    logout(hash)
    regs = status['PET']['LIST']['REG']
    dect = False
    for reg in regs:
        if reg['@type'] == '32':
            if dect:
                pass
            else:
                s[ALARM_MODES['armoutside']] = '0'
                s[ALARM_MODES['armnight']] = '0'
                s[ALARM_MODES['arm']] = '0'
            break
        elif reg['@type'] in ALARM_MODES.values():
            s[reg['@type']] = reg['@type']
            dect = True
    nd = dict(s)
    s.close()
    return nd

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=False,threaded=True,host='127.0.0.1',port='5000')
