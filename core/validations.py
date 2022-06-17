from enum import Enum

from haversine import haversine

from django.core.exceptions import ValidationError

from evs.models   import Station
from cafes.models import Cafe


class Range(Enum):
    limit_search = 20


class Category(Enum):
    STATION = 1
    CAFE    = 2
    

def validate_range(NE_latitude, SW_latitude, NE_longitude, SW_longitude):
    request_range = haversine((NE_latitude, NE_longitude), (SW_latitude, SW_longitude))
    if request_range > Range.limit_search.value:
        raise ValidationError("TOO_LARGE_RANGE", code=413)


def validate_search_position(user_latitude, user_longitude, category):
    if category == Category.STATION.value:
        stations = Station.objects.all().order_by("latitude", "longitude")
        MAX_LATITUDE  = stations.latest("latitude").latitude
        MIN_LATITUDE  = stations.earliest("latitude").latitude
        MAX_LONGITUDE = stations.latest("longitude").longitude
        MIN_LONGITUDE = stations.earliest("longitude").longitude

    elif category == Category.CAFE.value:
        cafes = Cafe.objects.all().order_by("latitude", "longitude")
        MAX_LATITUDE  = cafes.latest("latitude").latitude
        MIN_LATITUDE  = cafes.earliest("latitude").latitude
        MAX_LONGITUDE = cafes.latest("longitude").longitude
        MIN_LONGITUDE = cafes.earliest("longitude").longitude

    if (MIN_LATITUDE < user_latitude < MAX_LATITUDE) and (MIN_LONGITUDE < user_longitude < MAX_LONGITUDE):
        return user_latitude, user_longitude

    if user_latitude < MIN_LATITUDE:    
        reposition_latitude = MIN_LATITUDE
    elif MAX_LATITUDE < user_latitude:
        reposition_latitude = MAX_LATITUDE

    if  user_longitude < MIN_LONGITUDE:
        reposition_longitude = MIN_LONGITUDE
    elif MAX_LONGITUDE < user_longitude:
        reposition_longitude = MAX_LONGITUDE

    return float(reposition_latitude), float(reposition_longitude)