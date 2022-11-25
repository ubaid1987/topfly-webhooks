import json

import requests

from config import Settings
from utils.exception_handler import TopflyException

setting = Settings()

TOKEN = setting.TOKEN
TOKEN_LOGIN_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=token/login"
SEARCH_DRIVER_GROUP_ID_WITH_CODE_API = 'https://hst-api.wialon.com/wialon/ajax.html?svc=core/search_items&params={"spec":{"itemsType":"avl_resource","propType":"propitemname","propName":"drivers","propValueMask":"*","sortType":"drivers"},"force":1,"flags":256,"from":0,"to":0}'
DRIVER_FILE_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=file/list"
UNIT_FILE_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=file/list"
COMPANY_CARD_API = (
    "https://hst-api.wialon.com/wialon/ajax.html?svc=unit/update_hw_params"
)
SEND_COMMAND_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=core/batch"

GET_BACT_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=core/search_items"
GET_GEOFENCE_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=resource/get_zone_data"
CREATE_GEOFENCE_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=resource/update_zone"
DELETE_GEOFENCE_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=resource/update_zone"


class TopflyService:
    def __init__(self, sid: str, unitId: str, driver: str, date: str):
        self.sid = sid
        self.unitId = unitId
        self.driver = driver
        self.date = date

    @staticmethod
    def get_sid():
        params = {"token": TOKEN, "fl": 2}
        str_params = json.dumps(params)
        response = requests.get(f"{TOKEN_LOGIN_API}&params={str_params}")
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"TOKEN_LOGIN_API: Failed to get session id with reason {data['reason']}",
            )
        return data["eid"]

    def get_bact(self):
        params = json.dumps(
            {
                "spec": {
                    "itemsType": "avl_resource",
                    "propType": "propitemname",
                    "propName": "drivers",
                    "propValueMask": self.driver,
                    "sortType": "drivers",
                },
                "force": 1,
                "flags": 4,
                "from": 0,
                "to": 0,
            }
        )
        response = requests.get(
            f"{GET_BACT_API}&params={params}&sid={self.sid}")
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"GET_BACT_API: Failed.",
            )

        items = data["items"]
        if len(items) == 0:
            raise TopflyException(
                data=data,
                message=f"GET_BACT_API: items Array is empty",
            )

        return items[0]["bact"]

    def get_driver_c_code(self):
        response = requests.get(
            f"{SEARCH_DRIVER_GROUP_ID_WITH_CODE_API}&sid={self.sid}"
        )
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"SEARCH_DRIVER_GROUP_ID_WITH_CODE_API: Failed with error {data['error']}. Most likely because of invalid sid",
            )
        for item in data["items"]:
            drvrs = item.get("drvrs")
            if drvrs:
                for _, driver in drvrs.items():
                    if self.driver == driver["n"]:
                        return driver["c"]
        raise TopflyException(
            message=f"No driver found with name {self.driver}",
        )

    def get_unit_mt_epoch_time(self, unitId):
        params = json.dumps(
            {
                "itemId": unitId,
                "storageType": 2,
                "path": "/tachograph",
                "mask": "*",
                "recursive": False,
                "fullPath": False,
            }
        )
        response = requests.get(
            f"{UNIT_FILE_API}&params={params}&sid={self.sid}")
        filtered_list = []
        data_list = response.json()
        if "error" in data_list:
            raise TopflyException(
                data=data_list,
                message=f"UNIT_FILE_API: Failed with error {data_list['error']}. Most likely because of invalid sid",
            )
        for data in data_list:
            if "tacho_file.DDD" in data["n"]:
                filtered_list.append(data)
        if len(filtered_list) == 0:
            return None
        return filtered_list[-1]["mt"]

    def get_mt_epoch_time(self, c_code: str, bact):
        params = json.dumps(
            {
                "itemId": bact,
                "storageType": 2,
                "path": "tachograph/",
                "mask": "*",
                "recursive": False,
                "fullPath": False,
            }
        )
        response = requests.get(
            f"{DRIVER_FILE_API}&params={params}&sid={self.sid}")
        filtered_list = []
        data_list = response.json()
        if "error" in data_list:
            raise TopflyException(
                data=data_list,
                message=f"DRIVER_FILE_API: Failed with error {data_list['error']}. Most likely because of invalid sid",
            )
        for data in data_list:
            if c_code in data["n"]:
                filtered_list.append(data)
        if len(filtered_list) == 0:
            return None
        return filtered_list[-1]["mt"]

    def get_value_from_company_card_api(self):
        params = json.dumps(
            {"itemId": self.unitId, "hwId": "23036132",
                "fullData": 0, "action": "get"}
        )
        response = requests.get(
            f"{COMPANY_CARD_API}&params={params}&sid={self.sid}")
        data_list = response.json()
        if "error" in data_list:
            raise TopflyException(
                data=data_list,
                message=f"COMPANY_CARD_API: Failed with error {data_list['error']}. Most likely because of invalid sid",
            )
        name = "cc_sn"
        for data in data_list:
            if data["name"] == name:
                return data["value"]
        raise TopflyException(
            message=f"No Company sn found from company card API")

    def send_command(self):
        params = {
            "params": [
                {
                    "svc": "unit/exec_cmd",
                    "params": {
                        "itemId": self.unitId,
                        "commandName": "Scarico Tessera",
                        "linkType": "",
                        "param": "",
                        "timeout": 60,
                        "flags": 0,
                    },
                }
            ],
            "flags": 0,
        }
        str_params = json.dumps(params)
        response = requests.get(
            f"{SEND_COMMAND_API}&params={str_params}&sid={self.sid}"
        )
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"SEND_COMMAND_API: Failed",
            )
        return data

    def send_command_tachigrafo(self):
        params = {
            "params": [
                {
                    "svc": "unit/exec_cmd",
                    "params": {
                        "itemId": self.unitId,
                        "commandName": "Scarico Tachigrafo",
                        "linkType": "",
                        "param": "",
                        "timeout": 60,
                        "flags": 0,
                    },
                }
            ],
            "flags": 0,
        }
        str_params = json.dumps(params)
        response = requests.get(
            f"{SEND_COMMAND_API}&params={str_params}&sid={self.sid}"
        )
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"SEND_COMMAND_API: Failed",
            )
        return data


class Topflygeofence_create:
    def __init__(self, sid: str, trailer: str, lon: str, lat: str):
        self.sid = sid
        self.trailer = trailer
        self.lon = lon
        self.lat = lat

    @staticmethod
    def get_sid():
        params = {"token": TOKEN, "fl": 2}
        str_params = json.dumps(params)
        response = requests.get(f"{TOKEN_LOGIN_API}&params={str_params}")
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"TOKEN_LOGIN_API: Failed to get session id with reason {data['reason']}",
            )
        return data["eid"]

    def get_bact(self):
        params = json.dumps(
            {
                "spec": {
                    "itemsType": "avl_resource",
                    "propType": "propitemname",
                    "propName": "trailers",
                    "propValueMask": self.trailer,
                    "sortType": "trailers",
                },
                "force": 1,
                "flags": 4,
                "from": 0,
                "to": 0,
            }
        )
        response = requests.get(
            f"{GET_BACT_API}&params={params}&sid={self.sid}")
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"GET_BACT_API: Failed.",
            )

        items = data["items"]
        if len(items) == 0:
            raise TopflyException(
                data=data,
                message=f"GET_BACT_API: BACT unavailable, please check permissions/trailer name.",
            )

        return items[0]["bact"]

    def create(self, bact):
        params = json.dumps(
            {
                "n": self.trailer,
                "d": "",
                "t": 3,
                "w": 100,
                "f": 112,
                "c": 2568583984,
                "tc": 16733440,
                "ts": 12,
                "min": 0,
                "max": 18,
                "libId": "",
                "path": "",
                "p": [{"x": float(self.lon), "y": float(self.lat), "r": 100}],
                "itemId": bact,
                "id": 0,
                "callMode": "create",
                "flags": 0,
            }
        )
        response = requests.get(
            f"{CREATE_GEOFENCE_API}&params={params}&sid={self.sid}"
        )
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"CREATE_GEOFENCE_API: Failed to create geofence.",
            )
        return data


class Topflygeofence_delete:
    def __init__(self, sid: str, trailer: str):
        self.sid = sid
        self.trailer = trailer

    @staticmethod
    def get_sid():
        params = {"token": TOKEN, "fl": 2}
        str_params = json.dumps(params)
        response = requests.get(f"{TOKEN_LOGIN_API}&params={str_params}")
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"TOKEN_LOGIN_API: Failed to get session id with reason {data['reason']}",
            )
        return data["eid"]

    def get_bact(self):
        params = json.dumps(
            {
                "spec": {
                    "itemsType": "avl_resource",
                    "propType": "propitemname",
                    "propName": "trailers",
                    "propValueMask": self.trailer,
                    "sortType": "trailers",
                },
                "force": 1,
                "flags": 4,
                "from": 0,
                "to": 0,
            }
        )
        response = requests.get(
            f"{GET_BACT_API}&params={params}&sid={self.sid}")
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"GET_BACT_API: Failed.",
            )

        items = data["items"]
        if len(items) == 0:
            raise TopflyException(
                data=data,
                message=f"GET_BACT_API: BACT unavailable, please check permissions/trailer name.",
            )

        return items[0]["bact"]

    def get_geofence(self, bact):
        params = json.dumps(
            {
                "itemId": bact,
                "col": "*",
                "flags": 31
            }
        )
        response = requests.get(
            f"{GET_GEOFENCE_API}&params={params}&sid={self.sid}")
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"GET_GEOFENCE_API: Failed.",
            )

        geofence = []
        for item in data:
            if self.trailer in item["n"]:
                geofence.append(item["id"])

        if len(geofence) == 0:
            raise TopflyException(
                data=data,
                message=f"GET_GEOFENCE_API: No geofence found, please check permissions/trailer name.",
            )

        return geofence

    def delete(self, bact, geofence):
        params = []
        for i in geofence:
            params.append(json.dumps(
                {
                    "itemId": bact,
                    "id": i,
                    "callMode": "delete"
                }
            ))

        data = []
        for j in params:
            response = requests.get(
                f"{DELETE_GEOFENCE_API}&params={j}&sid={self.sid}")
            data.append(response.json())
            if "error" in data:
                raise TopflyException(
                    data=json.dumps(data),
                    message=f"DELETE_GEOFENCE_API: Failed to delete geofence.",
                )

        return json.dumps(data)
