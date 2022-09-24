import json
import requests

from config import Settings
from utils.exception_handler import TopflyException

setting = Settings()

TOKEN = setting.TOKEN
TOKEN_LOGIN_API = "https://hst-api.wialon.com/wialon/ajax.html?svc=token/login"
SEARCH_DRIVER_GROUP_ID_WITH_CODE_API = 'https://hst-api.wialon.com/wialon/ajax.html?svc=core/search_items&params={"spec":{"itemsType":"avl_resource","propType":"propitemname","propName":"drivers","propValueMask":"*","sortType":"drivers"},"force":1,"flags":256,"from":0,"to":0}'
DRIVER_FILE_API = 'https://hst-api.wialon.com/wialon/ajax.html?svc=file/list&params={"itemId":23080205,"storageType":2,"path":"tachograph/","mask":"*","recursive":false,"fullPath":false}'
COMPANY_CARD_API = (
    "https://hst-api.wialon.com/wialon/ajax.html?svc=unit/update_hw_params"
)


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

    def get_driver_c_code(self):
        response = requests.get(
            f"{SEARCH_DRIVER_GROUP_ID_WITH_CODE_API}&sid={self.sid}"
        )
        data = response.json()
        if "error" in data:
            raise TopflyException(
                data=data,
                message=f"SEARCH_DRIVER_GROUP_ID_WITH_CODE_API: Failed with error {data['error']}. Most likey beacuse of invalid sid",
            )
        drvrs = data["items"][0]["drvrs"]
        for _, driver in drvrs.items():
            if self.driver == driver["n"]:
                return driver["c"]
        raise TopflyException(
            message=f"No driver found with name {self.driver}",
        )

    def get_mt_epoch_time(self, c_code: str):
        response = requests.get(f"{DRIVER_FILE_API}&sid={self.sid}")
        filtered_list = []
        data_list = response.json()
        if "error" in data_list:
            raise TopflyException(
                data=data_list,
                message=f"DRIVER_FILE_API: Failed with error {data_list['error']}. Most likey beacuse of invalid sid",
            )
        for data in data_list:
            if c_code in data["n"]:
                filtered_list.append(data)
        return filtered_list[-1]["mt"]

    def get_value_from_company_card_api(self):
        params = json.dumps(
            {"itemId": self.unitId, "hwId": "23036132", "fullData": 0, "action": "get"}
        )
        response = requests.get(f"{COMPANY_CARD_API}&params={params}&sid={self.sid}")
        data_list = response.json()
        if "error" in data_list:
            raise TopflyException(
                data=data_list,
                message=f"COMPANY_CARD_API: Failed with error {data_list['error']}. Most likey beacuse of invalid sid",
            )
        name = "cc_sn"
        for data in data_list:
            if data["name"] == name:
                return data["value"]
        raise TopflyException(message=f"No Company sn found from company card API")

    def send_command(self):
        pass
