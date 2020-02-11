# VerisureEchoDevice
Turn your Verisure EU alarm into a Echo &amp; Alexa compatible device

**_NOTE:_** THIS PROJECT IS NOT IN ANY WAY ASSOCIATED WITH OR RELATED TO THE SECURITAS DIRECT-VERISURE GROUP COMPANIES. The information here and online is for educational and resource purposes only and therefore the developers do not endorse or condone any inappropriate use of it, and take no legal responsibility for the functionality or security of your alarms and devices.

This is basically a Flask App to use with fauxmo (https://pypi.org/project/fauxmo/) to emulate the Verisure EU alarm as a WEMO (Belkin) bulb/plug.

This has been configured to mimic Alarm modes into devices, so you can control:
* Totally arm the system (except the perimeter)
* Nigh mode
* Perimeter

No Skill is required as the WEMO support/discovery is already built-in the Echo devices (it actually requires having one in the same LAN than the device hosting this script). Once discovered and configured, you can easily turn on your alarm system with:

```Alexa, turn on Verisure outside```

# Installation/Usage

Modules required (install with pip)
* fauxmo
* Flask
* xmltodict
* Shelve
* Flask-Executor
* rq

Other stuff:
* Redis

Added RQ and Redis to support Alexa routines. The Verisure endpoint behaves quite weird if a routine asks for connecting the perimeter and the inside sensors at the same time.

Rename the config-sample.py to config.py and edit the file properly:

```
USER = 'username' # Username used in the webpage/mobile app
PWD = 'password' # Password used in the webpage/mobile app
NUMINST = '11111' # Installation Number (can be found in the WebPage)
PANEL = 'SDVFAST' # All recent models are SDVFAST
COUNTRY = 'ES' # ES, GB, FR, PT, IT
LANG = 'es' # es, en, fr, pt, it
SECONDS_BETWEEN_REQUESTS=1 # They detect flooding during interative actions, so be convervative.
```

As Alexa expects a quick response from the device, querying the Verisure backend to get the status is not an option. To solve that, the script uses a local file to store the current alarm status. If you use the magnetic keys, remotes or the mobile app as well, this file needs continuous updates and therefore some syncing method. You can add a cronjob like below to keep both the Verisure backend and your status in sync:

```
*/5 * * * * /usr/bin/curl http://localhost:5000/api/v1.0/synclog
```

To test the thing, run both this python script,fauxmo,redis and rq in different consoles and check the standard outputs

```
$ ./verisure.py
```

Edit the ```config-fauxmo.json``` file to change the names of the devices to your preference.

```
$ fauxmo -c config-fauxmo.json -vv
```

```
$ redis-server
```

```
$ rq worker
```

If everything works, daemonize to your taste.

Remember to edit the python file in order to use your username, installation number, region ...

# Caveats
* **YOU SHOULD TRACK** the activity of all your keys and remotes as the status sync is based on the activity log, not actually querying the panel !! You can easily do this on the Webpage or the Mobile App.
* It's strongly recommended that the computer/device running fauxmo has a fixed IP address.
* Turning off any of the alarm modes, obviusly turns off everything. This is not a limitation from this script, Verisure has configured their backend to work in that way. You can easily guess that behaviour if you use the mobile app frequently.
