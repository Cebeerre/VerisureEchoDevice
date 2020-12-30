#!/usr/bin/env python3
# -*- coding: utf-8 -*-
def VerisureAPIClient(action,user,pwd,numinst,panel,country,lang,rate):
    import requests
    import xmltodict
    from datetime import datetime
    import time
    BASE_URL='https://mob2217.securitasdirect.es:12010/WebService/ws.do'
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
    LOGIN_PAYLOAD = { 'Country': country, 'user':user, 'pwd': pwd, 'lang': lang }
    OP_PAYLOAD = { 'Country': country, 'user':user, 'pwd': pwd, 'lang': lang, 'panel': panel, 'numinst': numinst, 'callby': 'AND_61'}
    OUT_PAYLOAD = { 'Country': country, 'user':user, 'pwd': pwd, 'lang': lang, 'numinst': '(null)'}

    def call_verisure_get(method, parameters):
        time.sleep(rate)
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
        return output

    def generate_id():
        ID='AND_________________________'+user+datetime.now().strftime("%Y%m%d%H%M%S")
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

    def est():
        hash = get_login_hash()
        id = generate_id()
        status = op_verisure('EST', hash, id)
        logout(hash)
        return status

    def peri():
        hash = get_login_hash()
        id = generate_id()
        status = op_verisure('PERI', hash, id)
        logout(hash)
        return status

    def arm():
        hash = get_login_hash()
        id = generate_id()
        status = op_verisure('ARM', hash, id)
        logout(hash)
        return status

    def darm():
        hash = get_login_hash()
        id = generate_id()
        status = op_verisure('DARM', hash, id)
        logout(hash)
        return status

    def armnight():
        hash = get_login_hash()
        id = generate_id()
        status = op_verisure('ARMNIGHT', hash, id)
        logout(hash)
        return status

    def log():
        hash = get_login_hash()
        id = generate_id()
        payload = OP_PAYLOAD
        payload.update({'request': 'ACT_V2', 'hash':hash, 'ID':id, 'timefilter': '2', 'activityfilter': '0'})
        status = call_verisure_get('GET',payload)
        logout(hash)
        return status

    if action == 'arm':
        return arm()
    elif action == 'peri':
        return peri()
    elif action == 'armnight':
        return armnight()
    elif action == 'darm':
        return darm()
    elif action == 'est':
        return est()
    elif action == 'log':
        return log()
