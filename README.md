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
