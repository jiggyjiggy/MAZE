import requests
import pandas as pd

from datetime import datetime

from bs4 import BeautifulSoup

from django.conf import settings
from django.db   import transaction

from evs.models import ChargerHistory, Charger


def getChargerStatusAPI():
    URL = 'http://apis.data.go.kr/B552584/EvCharger/getChargerStatus'

    region = {
        '서울' : 11,
        '경기' : 41,
        '인천' : 28
    }

    MAX_SHIFT_SIZE = 10000
    totalCount     = 1e9
    UPDATE_PERIOD  = 1

    item_list = []
    
    print("------------------------------------------------------------------------------------------------------")
    print("crawling_start\n")
    crawling_start_time = datetime.now()
    for city, zcode in region.items():
        pageNo = 0
        print("city: ", city)

        while pageNo <= (totalCount / MAX_SHIFT_SIZE):
            pageNo += 1
            params = {
                'serviceKey' : settings.DECODED_SERVICE_KEY,
                'pageNo'     : pageNo,
                'numOfRows'  : MAX_SHIFT_SIZE,
                'period'     : UPDATE_PERIOD,
                'zcode'      : zcode
            }

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
                    "business_id"                    : item.find("busiId").text.strip(),
                    "station_id"                     : item.find("statId").text.strip(),
                    "index_in_station"               : int(item.find("chgerId").text.strip()),
                    "charging_status"                : int(item.find("stat").text.strip()),
                    "charger_status_update_datetime" : item.find("statUpdDt").text.strip()[0:4]+'-'+item.find("statUpdDt").text.strip()[4:6]+'-'+item.find("statUpdDt").text.strip()[6:8]+' '+item.find("statUpdDt").text.strip()[8:10]+":"+item.find("statUpdDt").text.strip()[10:12]+":"+item.find("statUpdDt").text.strip()[12:14] if item.find("statUpdDt").text else None,
                    "last_charging_start_datetime"   : item.find("lastTsdt").text.strip()[0:4]+'-'+item.find("lastTsdt").text.strip()[4:6]+'-'+item.find("lastTsdt").text.strip()[6:8]+' '+item.find("lastTsdt").text.strip()[8:10]+":"+item.find("lastTsdt").text.strip()[10:12]+":"+item.find("lastTsdt").text.strip()[12:14] if item.find("lastTsdt").text else None,
                    "last_charging_end_datetime"     : item.find("lastTedt").text.strip()[0:4]+'-'+item.find("lastTedt").text.strip()[4:6]+'-'+item.find("lastTedt").text.strip()[6:8]+' '+item.find("lastTedt").text.strip()[8:10]+":"+item.find("lastTedt").text.strip()[10:12]+":"+item.find("lastTedt").text.strip()[12:14] if item.find("lastTedt").text else None,
                    "now_charging_start_datetime"    : item.find("nowTsdt").text.strip()[0:4]+'-'+item.find("nowTsdt").text.strip()[4:6]+'-'+item.find("nowTsdt").text.strip()[6:8]+' '+item.find("nowTsdt").text.strip()[8:10]+":"+item.find("nowTsdt").text.strip()[10:12]+":"+item.find("nowTsdt").text.strip()[12:14] if item.find("nowTsdt").text else None, 
                })
    crawling_end_time = datetime.now()

    print("crawling_complete\n")
    print("crawling start time", crawling_start_time)
    print("crawling end time", crawling_end_time)
    print("crawling running time", crawling_end_time - crawling_start_time, "\n")

    response_df = pd.DataFrame(header_list)
    ev_df       = pd.DataFrame(item_list)

    print(response_df.head(len(header_list)))
    print(ev_df.head(len(item_list)))
    
    return item_list

def UpdateChargerHistory():

    item_list = getChargerStatusAPI()

    update_required = []

    print("\nstart update charger_histories table")
    update_start_time = datetime.now()

    for item in item_list:
        with transaction.atomic():
            try: 
                charger = Charger.objects.get(station_id=item["station_id"], index_in_station=item["index_in_station"])

                ChargerHistory.objects.create(
                    charger_status_update_datetime = item["charger_status_update_datetime"],
                    last_charging_start_datetime   = item["last_charging_start_datetime"],
                    last_charging_end_datetime     = item["last_charging_end_datetime"],
                    now_charging_start_datetime    = item["now_charging_start_datetime"],
                    charging_status_id             = item["charging_status"],
                    charger_id                     = charger.id
                )
            except Charger.DoesNotExist:
                update_required.append((item["station_id"], item["index_in_station"]))

    print("Update Required")
    print("(station_id, index_in_station)")
    print(*update_required, sep="\n")

    print("\nUpdateChargerHistory complete")
    update_end_time = datetime.now()
    print("update start time", update_start_time)
    print("update end time", update_end_time)
    print("update running time :", update_end_time - update_start_time)
    print("------------------------------------------------------------------------------------------------------")