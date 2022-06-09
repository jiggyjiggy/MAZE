from enum import Enum

from haversine import haversine

from django.http      import JsonResponse
from django.views     import View
from django.db.models import Q, Count, Case, When

from evs.models     import Station
from commons.models import Region


class ChargingStatus(Enum):
    COMMUNICATION_ABNOMAL = 1
    READY                 = 2
    CHARGING              = 3
    SUSPENDING            = 4
    INSPECTING            = 5
    NOT_CONFIRMED         = 9


class EVMapView(View):
    def get(self, request):
        SW_latitude      = float(request.GET["SW_latitude"])
        SW_longitude     = float(request.GET["SW_longitude"]) 
        NE_latitude      = float(request.GET["NE_latitude"])
        NE_longitude     = float(request.GET["NE_longitude"])
        outputs          = request.GET.getlist("outputs", None)
        charger_type_ids = request.GET.get("charger_type_ids", None)

        rectangle_boundary = (
                Q(latitude__range  = (SW_latitude, NE_latitude)) &
                Q(longitude__range = (SW_longitude, NE_longitude))
            )
            
        q = Q()

        if outputs:
            q |= Q(charger__output__in=outputs) 

        if charger_type_ids:
            q |= Q(charger__charger_type__code__in=charger_type_ids)

        near_stations = Station.objects\
            .annotate(total_charger=(Count("charger", distinct=True)))\
            .annotate(communication_abnomal_charger=(Count(Case(When(charger__chargerhistory__charging_status__code=ChargingStatus.COMMUNICATION_ABNOMAL.value, then=True)))))\
            .annotate(ready_charger=(Count(Case(When(charger__chargerhistory__charging_status__code=ChargingStatus.READY.value, then=True)))))\
            .annotate(charging_charger=(Count(Case(When(charger__chargerhistory__charging_status__code=ChargingStatus.CHARGING.value, then=True)))))\
            .annotate(suspending_charger=(Count(Case(When(charger__chargerhistory__charging_status__code=ChargingStatus.SUSPENDING.value, then=True)))))\
            .annotate(inspecting_charger=(Count(Case(When(charger__chargerhistory__charging_status__code=ChargingStatus.INSPECTING.value, then=True)))))\
            .annotate(not_confirmed_charger=(Count(Case(When(charger__chargerhistory__charging_status__code=ChargingStatus.NOT_CONFIRMED.value, then=True), When(charger__chargerhistory__charging_status=None, then=True)))))\
            .annotate(quick_charger=(Count(Case(When(charger__output__gte=30, then=True)))))\
            .annotate(slow_charger=(Count(Case(When(charger__output__lt=30, then=True)))))\
            .annotate(quick_charger_of_ready=(Count(Case(When(charger__output__gte=30, charger__chargerhistory__charging_status__code=ChargingStatus.READY.value, then=True)))))\
            .annotate(slow_charger_of_ready=(Count(Case(When(charger__output__lt=30, charger__chargerhistory__charging_status__code=ChargingStatus.READY.value, then=True)))))\
            .filter(rectangle_boundary)\
            .filter(q)

        results = [{
            "id"                        : station.id,
            "name"                      : station.name,
            "detail_location"           : station.detail_location,
            "road_name_address"         : station.road_name_address,
            "latitude"                  : station.latitude,
            "longitude"                 : station.longitude,
            "hours_of_operation"        : station.hours_of_operation,
            "business_id"               : station.business_id,
            "business_name"             : station.business_name,
            "business_manamgement_name" : station.business_manamgement_name,
            "business_call"             : station.business_call,
            "parking_free_yes_or_no"    : station.parking_free_yes_or_no,
            "parking_detail"            : station.parking_detail,
            "limit_yes_or_no"           : station.limit_yes_or_no,
            "limit_detail"              : station.limit_detail,
            "delete_yes_or_no"          : station.delete_yes_or_no,
            "delete_detail"             : station.delete_detail,
            "category"                  : station.category.type,
            "region"                    : station.region.city,
            "chargers"                  : {
                "count_of_status"       : {
                    "total_charger"                 : station.total_charger,
                    "communication_abnomal_charger" : station.communication_abnomal_charger,
                    "ready_charger"                 : station.ready_charger,
                    "charging_charger"              : station.charging_charger,
                    "suspending_charger"            : station.suspending_charger,
                    "inspecting_charger"            : station.inspecting_charger,
                    "not_confirmed_charger"         : station.not_confirmed_charger
                },
                "quick_and_slow" : {
                    "of_total_charger" : {
                        "quick" : station.quick_charger,
                        "slow"  : station.slow_charger
                    },
                    "of_ready_charger" : {
                        "quick" : station.quick_charger_of_ready,
                        "slow"  : station.slow_charger_of_ready
                    }
                },
                "chargers_in_station" : [{
                    "id"               : charger.id,
                    "index_in_station" : charger.index_in_station,
                    "output"           : charger.output,
                    "method"           : charger.method,
                    "charger_type"     : charger.charger_type.explanation,
                    "charging_status"  : charger.chargerhistory_set.last().charging_status.explanation if charger.chargerhistory_set.exists() else "상태미확인"
                } for charger in station.charger_set.all()]
            }
        } for station in near_stations]

        return JsonResponse({"results" : results}, status=200)


class SearchNearestEVView(View):
    def get(self, request):
        # 1 degree of longitude = 111.19 km
        # 1 degree of latitude in seoul (longitude: 37 degree) = 88.80 km
        LATITUDE_100m  = 0.0008993614533681087 
        LONGITUDE_100m = 0.0011261261261261261

        user_latitude  = float(request.GET.get("user_latitude", None))
        user_longitude = float(request.GET.get("user_longitude", None)) 
        user_position  = (user_latitude, user_longitude)

        nearest_station = True
        range          = 0

        while nearest_station:
            range += 1
            search_range = (
                    Q(latitude__range  = (user_latitude - LATITUDE_100m * range, user_latitude + LATITUDE_100m * range)) &
                    Q(longitude__range = (user_longitude - LONGITUDE_100m * range, user_longitude + LONGITUDE_100m * range))
                )

            stations = Station.objects.filter(search_range)
            
            distances = [haversine(user_position, (station.latitude, station.longitude)) for station in stations]
            if distances:
                break

        nearest_distance = min(distances)
        nearest_station  = stations[distances.index(nearest_distance)]

        results = {
            "search_range" : {
                "km" : 0.1 * range
            },
            "nearest_station": {
                    "km"        : nearest_distance,
                    "id"        : nearest_station.id,
                    "name"      : nearest_station.name,
                    "latitude"  : nearest_station.latitude,
                    "longitude" : nearest_station.longitude
                }
            }

        return JsonResponse({"results" : results}, status=200)


class EVAdminView(View):
    def get(self, request):
        regions  = request.GET.getlist("regions", None)

        if regions:
            regions = Q(city__in = regions)

        regions = Region.objects\
            .annotate(total_station=Count("station", distinct=True))\
            .annotate(total_charger=Count("station__charger", distinct=True))\
            .annotate(communication_abnomal_charger=(Count(Case(When(station__charger__chargerhistory__charging_status__code=ChargingStatus.COMMUNICATION_ABNOMAL.value, then=True)))))\
            .annotate(ready_charger=(Count(Case(When(station__charger__chargerhistory__charging_status__code=ChargingStatus.READY.value, then=True)))))\
            .annotate(charging_charger=(Count(Case(When(station__charger__chargerhistory__charging_status__code=ChargingStatus.CHARGING.value, then=True)))))\
            .annotate(suspending_charger=(Count(Case(When(station__charger__chargerhistory__charging_status__code=ChargingStatus.SUSPENDING.value, then=True)))))\
            .annotate(inspecting_charger=(Count(Case(When(station__charger__chargerhistory__charging_status__code=ChargingStatus.INSPECTING.value, then=True)))))\
            .annotate(not_confirmed_charger=(Count(Case(When(station__charger__chargerhistory__charging_status__code=ChargingStatus.NOT_CONFIRMED.value, then=True), When(station__charger__chargerhistory__charging_status=None, then=True)))))\
            .filter(regions)

        results = [{
            "chargers" : {
                "region"          : region.city,
                "count_of_status" : {
                    "total_station"                 : region.total_station,
                    "total_charger"                 : region.total_charger,
                    "communication_abnomal_charger" : region.communication_abnomal_charger,
                    "ready_charger"                 : region.ready_charger,
                    "charging_charger"              : region.charging_charger,
                    "suspending_charger"            : region.suspending_charger,
                    "inspecting_charger"            : region.inspecting_charger,
                    "not_confirmed_charger"         : region.not_confirmed_charger
                }
            }
        } for region in regions]

        return JsonResponse({"results" : results}, status=200)