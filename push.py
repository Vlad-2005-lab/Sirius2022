import requests
import time
from random import choice

address = " https://8668-85-174-194-250.eu.ngrok.io"
req = None
# for i in range(2, 9):
#     req = requests.request("POST", f"{address}/api/add", json={"name": f"printer №{i}", "okey": False})
#     # req = requests.request("POST", f"{address}/api/delete", json={"id": i})
#     print(req)
#     time.sleep(1)
# req = requests.request("POST", f"{address}/api/add", json={"name": "printer", "okey": choice([True, False])})
# req = requests.request("POST", f"{address}/api/update", json={"id": 1, "okey": False})
# req = requests.request("POST", f"{address}/api/update", json={"id": 2, "okey": True})
# req = requests.request("POST", f"{address}/api/update", json={"id": 4, "okey": True})
# req = requests.request("POST", f"{address}/api/update", json={"id": 5, "okey": True})
# req = requests.request("POST", f"{address}/api/update", json={"id": 6, "okey": True})
# req = requests.request("POST", f"{address}/api/update", json={"id": 7, "okey": True})
# req = requests.request("POST", f"{address}/api/check_uid", json={"uid": "228"})
# req = requests.request("POST", f"{address}/api/create_employee", json={"tg_id": 228, "name": "abc", "uid": "1236"})
# req = requests.request("GET", f"{address}/api/get_all_devices")
# req = requests.request("GET", f"{address}/api/get_all_employees")
a = """1	852437633	vlad	8648341F	0	2022-10-28 10:34:40.285257	
2	271668384	Николай	CC656C26	1		
3	1555839113	Арина	F6F56791	1		
4	535219500	Саша	49D029C6	0		"""
# try:
#     print(req.json())
# except Exception:
#     print(req.text)
