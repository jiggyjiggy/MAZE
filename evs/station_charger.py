import requests
import pandas as pd

from enum     import Enum
from datetime import datetime

from bs4 import BeautifulSoup

from django.conf import settings
from django.db   import transaction

from evs.models import Station, Charger


class Category(Enum):
    COFFEESHOP = 1
    EV         = 2


def get_charger_info_API():
    URL = 'http://apis.data.go.kr/B552584/EvCharger/getChargerInfo'

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
    print("charger info crawling start\n")
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
                    "station_id"                : item.find("statId").text.strip(),
                    "station_name"              : item.find("statNm").text.strip(),
                    "location"                  : item.find("location").text.strip(),
                    "road_name_address"         : item.find("addr").text.strip(),
                    "latitude"                  : float(item.find("lat").text.strip()),
                    "longitude"                 : float(item.find("lng").text.strip()),
                    "hours_of_operation"        : item.find("useTime").text.strip(),
                    "index_in_station"          : int(item.find("chgerId").text.strip()),
                    "charging_status"           : int(item.find("stat").text.strip()),
                    "charger_type"              : int(item.find("chgerType").text.strip()),
                    "output"                    : int(item.find("output").text.strip()) if item.find("output").text != '' else None,
                    "method"                    : item.find("method").text.strip(),
                    "parking_free_yes_or_no"    : item.find("parkingFree").text.strip(),
                    "parking_detail"            : item.find("note").text.strip(),
                    "limit_yes_or_no"           : item.find("limitYn").text.strip(),
                    "limit_detail"              : item.find("limitDetail").text.strip(),
                    "delete_yes_or_no"          : item.find("delYn").text.strip(),
                    "delete_detail"             : item.find("delDetail").text.strip(),
                    "business_id"               : item.find("busiId").text.strip(),
                    "business_name"             : item.find("bnm").text.strip(),
                    "business_manamgement_name" : item.find("busiNm").text.strip(),
                    "business_call"             : item.find("busiCall").text.strip(),
                    "zcode"                     : int(item.find("zcode").text.strip())
                })

    crawling_end_time = datetime.now()

    print("charger info crawling complete\n")
    print("crawling start time", crawling_start_time)
    print("crawling end time", crawling_end_time)
    print("crawling running time", crawling_end_time - crawling_start_time, "\n")

    response_df = pd.DataFrame(header_list)
    ev_df       = pd.DataFrame(item_list)

    print(response_df.head(len(header_list)))
    print(ev_df.head(len(item_list)))
    
    return item_list

def update_stations_and_chargers():

    item_list = get_charger_info_API()

    print("\nstart update tables; stations and chargers")
    update_start_time = datetime.now()

    for item in item_list:
        with transaction.atomic():
            Station.objects.update_or_create(
                id = item["station_id"],
                defaults={
                    "name"                      : item["station_name"],
                    "detail_location"           : item["location"],
                    "road_name_address"         : item["road_name_address"],
                    "latitude"                  : item["latitude"],
                    "longitude"                 : item["longitude"],
                    "hours_of_operation"        : item["hours_of_operation"],
                    "business_id"               : item["business_id"],
                    "business_name"             : item["business_name"],
                    "business_manamgement_name" : item["business_manamgement_name"],
                    "business_call"             : item["business_call"],
                    "parking_free_yes_or_no"    : item["parking_free_yes_or_no"],
                    "parking_detail"            : item["parking_detail"],
                    "limit_yes_or_no"           : item["limit_yes_or_no"],
                    "limit_detail"              : item["limit_detail"],
                    "delete_yes_or_no"          : item["delete_yes_or_no"],
                    "delete_detail"             : item["delete_detail"],
                    "category_id"               : Category.EV.value,
                    "region_id"                 : item["zcode"]
                }
            )
            Charger.objects.update_or_create(
                index_in_station = item["index_in_station"],
                station_id       = item["station_id"],
                defaults={
                    "output"             : item["output"],
                    "method"             : item["method"],
                    "charger_type_id"    : item["charger_type"],
                    "charging_status_id" : item["charging_status"]
               }
            )
        
    print("\nUpdateChargerHistory complete\n")
    update_end_time = datetime.now()
    print("update start time", update_start_time)
    print("update end time", update_end_time)
    print("update running time :", update_end_time - update_start_time)
    print("------------------------------------------------------------------------------------------------------")