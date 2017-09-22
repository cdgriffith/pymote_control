# Pymote Control Center 

```
__________________________
|        .::::::::.       |
|        :::  :::::       |
|        ```````:::       |
|    .::::::::::::: ii,   |
|  :::::::::::::::: iiii  |
|  ::::: ,,,,,,,,,,iiiii  |
|    `:: iiiiiiiiiiii`    |
|        iii,,,,,,,       |
|        iiiii  iii       |
|        `iiiiiiii`       |
|                         |
|  (PWR)                  |
|                         |
|  ( 1 )   ( 2 )   ( 3 )  |
|                         |
|  ( 4 )   ( 5 )   ( 6 )  |
|                         |
|  ( 7 )   ( 8 )   ( 9 )  |
|                         |
|          ( 0 )          |
|                         |
|_________________________|

```

## Install 

Requires: 

* Python 3.6+ 
* Linux (might work with Windows, untested)

Remotely execute and check on commands. Start it up with `python3.6 pymote_control.py`
after installing everything in `requirements.txt`

To install, download as a zip file and move to a perminiate directory 
of your choice, in this example we will use `/opt/pymote_control`.
You **must** be `root` to install. 

```bash
mkdir -p /opt/pymote_control
cd /opt/pymote_control
wget https://github.com/cdgriffith/pymote_control/archive/master.zip
unzip master.zip 
python3.6 setup.py install 
```

## Example 

```python
import time 
import requests 

req = requests.post("http://localhost:8000/v1/program/", json={"command": "sleep 10; echo 'hi'"})
print(req.json())
{'pid': '7659'}

print(requests.get(f"http://localhost:8000/v1/program/{req.json()['pid']}").json())
{'stdout': '', 'stderr': '', 'finished': False, 'return_code': None}

time.sleep(10)

print(requests.get(f"http://localhost:8000/v1/program/{req.json()['pid']}").json())
{'stdout': 'hi\n', 'stderr': '', 'finished': True, 'return_code': 0}
```

Endpoints: 

* POST   /v1/program/            | New command
* GET    /v1/program/<pid>       | View the logs
* POST   /v1/program/<pid>/stop  | terminate a program
* DELETE /v1/program/<pid>       | terminate and delete all files

