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

Remotely execute and check on commands. Start it up with `python3.6 pymote_control.py`
after installing everything in `requirements.txt`



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