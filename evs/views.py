from django.http      import JsonResponse
from django.views     import View
from django.db.models import Q

from evs.models import Station


class EVMapView(View):
    def get(self, request):
        SW_latitude  = float(request.GET.get("SW_latitude", None))
        SW_longitude = float(request.GET.get("SW_longitude", None)) 
        NE_latitude  = float(request.GET.get("NE_latitude", None))
        NE_longitude = float(request.GET.get("NE_longitude", None))

        rectangle_boundary = (
                Q(latitude__range  = (SW_latitude, NE_latitude)) &
                Q(longitude__range = (SW_longitude, NE_longitude))
            )
        
        near_stations = Station.objects.filter(rectangle_boundary)

        results = [{
            "id"                        : near_station.id,
            "name"                      : near_station.name,
            "detail_location"           : near_station.detail_location,
            "road_name_address"         : near_station.road_name_address,
            "latitude"                  : near_station.latitude,
            "longitude"                 : near_station.longitude,
            "hours_of_operation"        : near_station.hours_of_operation,
            "business_id"               : near_station.business_id,
            "business_name"             : near_station.business_name,
            "business_manamgement_name" : near_station.business_manamgement_name,
            "business_call"             : near_station.business_call,
            "parking_free_yes_or_no"    : near_station.parking_free_yes_or_no,
            "parking_detail"            : near_station.parking_detail,
            "limit_yes_or_no"           : near_station.limit_yes_or_no,
            "limit_detail"              : near_station.limit_detail,
            "delete_yes_or_no"          : near_station.delete_yes_or_no,
            "delete_detail"             : near_station.delete_detail,
            "category"                  : near_station.category.type,
            "zcode"                     : near_station.zcode.city
        } for near_station in near_stations]

        return JsonResponse({"results" : results}, status=200)