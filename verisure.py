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
from flask_executor import Executor

r"""
https://github.com/Cebeerre/VerisureEchoDevice

# VerisureEchoDevice
Turn your Verisure EU alarm into a Echo &amp; Alexa device

THIS PROJECT IS NOT IN ANY WAY ASSOCIATED WITH OR RELATED TO THE SECURITAS DIRECT-VERISURE GROUP COMPANIES.

This is basically a Flask App to use with fauxmo (https://pypi.org/project/fauxmo/) to emulate the Verisure EU alarm as a WEMO (Belkin) bulb/plug.

# Installation/Usage 

Modules required (install with pip)
* fauxmo
* Flask
* xmltodict
* Shelve
* Flask-Executor

As Alexa expects a quick response from the device, querying the Verisure backend to get the status is not an option. To solve that, the script uses a local file to store the current alarm status. If you use the magnetic keys, remotes or the mobile app as well, this file needs continuous updates and therefore some syncing method. You can add a cronjob like below to keep both the Verisure backend and your status in sync:

```
*/5 * * * * /usr/bin/curl http://localhost:5000/api/v1.0/synclog
```

To test the thing, run both this python script and fauxmo in different consoles and check the standard outputs

```
$ ./verisure.py 
```

```
$ fauxmo -c config.json -vv
```

If everything works, daemonize to your taste.

Remember to edit the python file in order to use your username, installation number, region ...

It's strongly recommended that the computer/device running fauxmo has a fixed IP address.

Use the below as fauxmo config.json file. Edit the names to match your language/preference:

```
{
    "FAUXMO": {
        "ip_address": "auto"
    },
    "PLUGINS": {
        "SimpleHTTPPlugin": {
            "DEVICES": [
                {
                    "port": 12345,
                    "on_cmd": "http://localhost:5000/api/v1.0/armoutside",
                    "off_cmd": "http://localhost:5000/api/v1.0/disarm",
                    "state_cmd": "http://localhost:5000/api/v1.0/status?alarm=40",
                    "state_response_on": "\"status\":\"40\"",
                    "state_response_off": "\"status\":\"0\"",
                    "method": "GET",
                    "name": "Securitas Perimetral"
                },
                {
                    "port": 12346,
                    "on_cmd": "http://localhost:5000/api/v1.0/armnight",
                    "off_cmd": "http://localhost:5000/api/v1.0/disarm",
                    "state_cmd": "http://localhost:5000/api/v1.0/status?alarm=46",
                    "state_response_on": "\"status\":\"46\"",
                    "state_response_off": "\"status\":\"0\"",
                    "method": "GET",
                    "name": "Securitas Noche"
                },
                {
                    "port": 12347,
                    "on_cmd": "http://localhost:5000/api/v1.0/arm",
                    "off_cmd": "http://localhost:5000/api/v1.0/disarm",
                    "state_cmd": "http://localhost:5000/api/v1.0/status?alarm=31",
                    "state_response_on": "\"status\":\"31\"",
                    "state_response_off": "\"status\":\"0\"",
                    "method": "GET",
                    "name": "Securitas Interior"
                }
            ]
        }
    }
}
```

Cebeerre/VerisureEchoDevice is licensed under the

MIT License
"""

############################################################
# Adjust for each
############################################################

USER = 'username' # Username in the WebPage
PWD = 'password' # Password in the WebPage
NUMINST = '11111' # Installation Number (can be found in the WebPage)
PANEL = 'SDVFAST' # All recent models are SDVFAST
COUNTRY = 'ES' # ES, GB, FR, PT, IT 
LANG = 'es' # es, en, fr, pt, it 
SECONDS_BETWEEN_REQUESTS=1 # They detect flooding during interative actions, so be convervative.

############################################################
# Do not edit from here
############################################################
LOGIN_PAYLOAD = { 'Country': COUNTRY, 'user':USER, 'pwd': PWD, 'lang': LANG }
OP_PAYLOAD = { 'Country': COUNTRY, 'user':USER, 'pwd': PWD, 'lang': LANG, 'panel': PANEL, 'numinst': NUMINST}
OUT_PAYLOAD = { 'Country': COUNTRY, 'user':USER, 'pwd': PWD, 'lang': LANG, 'numinst': '(null)'}
ALARM_MODES = { 'armoutside': '40', 'armnight': '46', 'arm': '31'}
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
        synclog()
        output = jsonify(success=True)
    else:
        abort(404)
    return output

def set_alarm_status(action):
    s = shelve.open('verisure_shelf', writeback=True)
    if action == 'disarm':
        s[ALARM_MODES['armoutside']] = '0'
        s[ALARM_MODES['armnight']] = '0'
        s[ALARM_MODES['arm']] = '0'
    else:
        s[ALARM_MODES[action]] = ALARM_MODES[action]
    s.close()

def return_alarm_status(action):
    s = shelve.open('verisure_shelf', writeback=True)
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
    s = shelve.open('verisure_shelf', writeback=True)
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
        elif reg['@type'] == alarm:
            s[reg['@type']] = reg['@type']
            dect = True
    s.close()

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=False,threaded=True,host='127.0.0.1',port='5000')
