import requests
import pandas as pd

from datetime import datetime

from bs4 import BeautifulSoup

from django.conf import settings
from django.db   import transaction

from evs.models import ChargerHistory, Charger # Station


def getChargerStatusAPI():
    URL = 'http://apis.data.go.kr/B552584/EvCharger/getChargerStatus'

    UPDATE_PERIOD = 10

    region = {
        '서울' : 11,
        '경기' : 41,
        '인천' : 28
    }

    MAX_SHIFT_SIZE = 10000
    totalCount     = 1e9

    item_list = []

    print("start crawling")
    for city, zcode in region.items():
        pageNo = 0
        print("city: ", city)
        print("zcode: ", zcode)

        while pageNo <= (totalCount / MAX_SHIFT_SIZE):
            pageNo += 1
            params = {
                'serviceKey' : settings.DECODED_SERVICE_KEY,
                'pageNo'     : pageNo,
                'numOfRows'  : MAX_SHIFT_SIZE,
                'period'     : UPDATE_PERIOD,
                'zcode'      : zcode
            }

            print("totalCount / MAX_SHIFT_SIZE: ", (totalCount / MAX_SHIFT_SIZE))
            print("pageNo: ", pageNo)

            response = requests.get(URL, params=params)

            content = response.text

            xml = BeautifulSoup(content, "lxml-xml")

            header = xml.find("header")
            items  = xml.find("items")

            header_list = [{
                "resultCode" : header.find("resultCode").text.strip(),
                "resultMsg"  : header.find("resultMsg").text.strip(),
                "totalCount" : header.find("totalCount").text.strip(),
                "pageNo"     : header.find("pageNo").text.strip(),
                "numOfRows"  : header.find("numOfRows").text.strip(),
            }]
            totalCount = int(header.find("totalCount").text.strip())

            for item in items:
                item_list.append({
                    "business_id"                    : int(item.find("busiId").text.strip()),
                    "station_id"                     : int(item.find("statId").text.strip()),
                    "index_in_station"               : int(item.find("chgerId").text.strip()),
                    "charging_status"                : int(item.find("stat").text.strip()),
                    "charger_status_update_datetime" : datetime.strptime(item.find("statUpdDt").text.strip(), '%Y%m%d%f'),
                    "last_charging_start_datetime"   : datetime.strptime(item.find("lastTsdt").text.strip(), '%Y%m%d%f'),
                    "last_charging_end_datetime"     : datetime.strptime(item.find("lastTedt").text.strip(), '%Y%m%d%f'),
                    "now_charging_start_datetime"    : datetime.strptime(item.find("nowTsdt").text.strip(), '%Y%m%d%f'),  
                })
    print("end crawling")

    response_df = pd.DataFrame(header_list)
    ev_df       = pd.DataFrame(item_list)

    print(response_df.head(len(header_list)))
    print(ev_df.head(len(item_list)))
    
    return item_list

getChargerStatusAPI()

def UpdateChargerHistory(item_list):
    print("start update charger_histories table")
    for item in item_list:
        with transaction.atomic():
            # charger의 station_id는 Station field 에서 business_id 로 index 해서 찾는게 빠를수도? (나중에 해보기)
            charger = Charger.objects.filter(station_id=item["station_id"], index_in_station=item["index_in_station"])

            ChargerHistory.objects.create(
                charger_status_update_datetime = item["charger_status_update_datetime"],
                last_charging_start_datetime   = item["last_charging_start_datetime"],
                last_charging_end_datetime     = item["last_charging_end_datetime"],
                now_charging_start_datetime    = item["now_charging_start_datetime"],
                charging_status                = item["charging_status"],
                charger                        = charger.id
            )
 