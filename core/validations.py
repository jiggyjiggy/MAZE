from enum import Enum

from django.core.exceptions import ValidationError

from evs.models   import Station
from cafes.models import Cafe

class Length(Enum):
    # 1 degree of longitude = 111.19 km
    # 1 degree of latitude in seoul (longitude: 37 degree) = 88.80 km
    LATITUDE_100m  = 0.0008993614533681087 
    LONGITUDE_100m = 0.0011261261261261261
    LATITUDE_3km   = 0.026980843601043
    LONGITUDE_3km  = 0.033783783783784


class Category(Enum):
    STATION = 1
    CAFE    = 2
    

def validate_range(NE_latitude, SW_latitude, NE_longitude, SW_longitude):
    if (NE_latitude - SW_latitude > Length.LATITUDE_100m.value) or (NE_longitude - SW_longitude > Length.LONGITUDE_3km.value):
        raise ValidationError("TOO_BIG_RANGE", code=413)


def validate_search_position(user_latitude, user_longitude, category):
    if category == Category.STATION.value:
        stations = Station.objects.order_by("latitude", "longitude")
        print(stations)
        # MAX_LATITUDE_STATION  = stations.last("latitude").latitude
        # MIN_LATITUDE_STATION  = stations.first("latitude").latitude
        # MAX_LONGITUDE_STATION = stations.last("longitude").longitude
        # MIN_LONGITUDE_STATION = stations.first("longitude").longitude
        MAX_LATITUDE_STATION  = stations.last().latitude
        MIN_LATITUDE_STATION  = stations.first().latitude
        MAX_LONGITUDE_STATION = stations.last().longitude
        MIN_LONGITUDE_STATION = stations.first().longitude

    elif category == Category.CAFE:
        cafes = Cafe.objects.order_by("latitude", "longitude")
        MAX_LATITUDE_STATION  = cafes.last("latitude").latitude
        MIN_LATITUDE_STATION  = cafes.first("latitude").latitude
        MAX_LONGITUDE_STATION = cafes.last("longitude").longitude
        MIN_LONGITUDE_STATION = cafes.first("longitude").longitude

    if user_latitude < MIN_LATITUDE_STATION:    
        reposition_latitude = MIN_LATITUDE_STATION
    elif MAX_LATITUDE_STATION < user_latitude:
        reposition_latitude = MAX_LATITUDE_STATION

    if  user_longitude < MIN_LONGITUDE_STATION:
        reposition_longitude = MIN_LONGITUDE_STATION
    elif MAX_LONGITUDE_STATION < user_longitude:
        reposition_longitude = MAX_LONGITUDE_STATION

        return reposition_latitude, reposition_longitude