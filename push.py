import requests
import time
from random import choice

address = "http://192.168.56.1:8080"
# for i in range(1, 8):
#     req = requests.request("POST", f"{address}/api/add", json={"name": "printer", "okey": choice([True, False])})
#     # req = requests.request("POST", f"{address}/api/delete", json={"id": i})
#     print(req)
#     time.sleep(1)
# req = requests.request("POST", f"{address}/api/add", json={"name": "printer", "okey": choice([True, False])})
# req = requests.request("POST", f"{address}/api/update", json={"id": 4, "okey": False})
# req = requests.request("POST", f"{address}/api/check_uid", json={"uid": "228"})
# req = requests.request("POST", f"{address}/api/create_employee", json={"tg_id": 228, "name": "abc", "uid": "1236"})
# req = requests.request("GET", f"{address}/api/get_all_devices")
req = requests.request("GET", f"{address}/api/get_all_employees")
try:
    print(req.json())
except Exception:
    print(req.text)
