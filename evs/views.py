from enum import Enum

from haversine import haversine

from django.http            import JsonResponse
from django.views           import View
from django.core.exceptions import ValidationError
from django.db.models       import Q, Count, Case, When, Prefetch

from evs.models       import Station, Charger
from commons.models   import Region
from core.validations import validate_range, validate_search_position


class ChargingStatus(Enum):
    COMMUNICATION_ABNOMAL = 1
    READY                 = 2
    CHARGING              = 3
    SUSPENDING            = 4
    INSPECTING            = 5
    NOT_CONFIRMED         = 9


class Usable(Enum):
    YES = "YES"
    NO  = "NO"
    

class Length(Enum):
    # 1 degree of longitude = 111.19 km
    # 1 degree of latitude in seoul (longitude: 37 degree) = 88.80 km
    LATITUDE_100m  = 0.0008993614533681087 
    LONGITUDE_100m = 0.0011261261261261261


class Category(Enum):
    STATION = 1
    CAFE    = 2


class EVMapView(View):
    def get(self, request):
        try:
            SW_latitude      = float(request.GET["SW_latitude"])
            SW_longitude     = float(request.GET["SW_longitude"]) 
            NE_latitude      = float(request.GET["NE_latitude"])
            NE_longitude     = float(request.GET["NE_longitude"])
            outputs          = request.GET.getlist("outputs", None)
            charger_type_ids = request.GET.get("charger_type_ids", None)
            usable           = request.GET.get("usable", None)

            validate_range(NE_latitude, SW_latitude, NE_longitude, SW_longitude)

            rectangle_boundary = (
                    Q(latitude__range  = (SW_latitude, NE_latitude)) &
                    Q(longitude__range = (SW_longitude, NE_longitude))
                )
                
            q1 = Q()
            q2 = Q()

            if outputs:
                q1 |= Q(charger__output__in=outputs) 

            if charger_type_ids:
                q1 |= Q(charger__charger_type__code__in=charger_type_ids)

            if usable == Usable.YES.value:
                q2 = Q(ready_charger__gte=1)

            near_stations = Station.objects\
                .select_related("category", "region")\
                .prefetch_related(
                        Prefetch("charger_set", queryset=Charger.objects.all().select_related("charger_type", "station", "charging_status"))
                    )\
                .filter(rectangle_boundary)\
                .filter(q1)\
                .annotate(ready_charger=Count("charger__charging_status", Case(When(charger__charging_status=ChargingStatus.READY.value, then=True))))\
                .filter(q2)

            target_stations = Station.objects\
                .filter(rectangle_boundary)\
                .annotate(total_charger=Count("charger"))\
                .annotate(communication_abnomal_charger=Count("charger__charging_status", Case(When(charger__charging_status=ChargingStatus.COMMUNICATION_ABNOMAL.value, then=True))))\
                .annotate(ready_charger=Count("charger__charging_status", Case(When(charger__charging_status=ChargingStatus.READY.value, then=True))))\
                .annotate(charging_charger=Count("charger__charging_status", Case(When(charger__charging_status=ChargingStatus.CHARGING.value, then=True))))\
                .annotate(suspending_charger=Count("charger__charging_status", Case(When(charger__charging_status=ChargingStatus.SUSPENDING.value, then=True))))\
                .annotate(inspecting_charger=Count("charger__charging_status", Case(When(charger__charging_status=ChargingStatus.INSPECTING.value, then=True))))\
                .annotate(not_confirmed_charger=Count("charger__charging_status", Case(When(charger__charging_status=ChargingStatus.NOT_CONFIRMED.value, then=True))))\
                .annotate(quick_charger=Count("charger", Case(When(charger__output__gte=30, then=True))))\
                .annotate(slow_charger=Count("charger", Case(When(charger__output__lt=30, then=True))))\
                .annotate(quick_charger_of_ready=Count(Case(When(charger__output__gte=30, charger__charging_status=ChargingStatus.READY.value, then=True))))\
                .annotate(slow_charger_of_ready=Count(Case(When(charger__output__lt=30, charger__charging_status=ChargingStatus.READY.value, then=True))))\
                .filter(q2)

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
                "chargers"                  : [{
                    "usable_of_all"       : Usable.YES.value if target_station.ready_charger else Usable.NO.value,
                    "usable_by_filtering" : Usable.YES.value if station.ready_charger else Usable.NO.value,
                    "count_of_status"     : {
                        "total_charger"                 : target_station.total_charger, 
                        "communication_abnomal_charger" : target_station.communication_abnomal_charger,
                        "ready_charger"                 : target_station.ready_charger,
                        "charging_charger"              : target_station.charging_charger,
                        "suspending_charger"            : target_station.suspending_charger,
                        "inspecting_charger"            : target_station.inspecting_charger,
                        "not_confirmed_charger"         : target_station.not_confirmed_charger,
                    },
                    "quick_and_slow" : {
                        "of_total_charger" : {
                            "quick" : target_station.quick_charger,
                            "slow"  : target_station.slow_charger
                        },
                        "of_ready_charger" : {
                            "quick" : target_station.quick_charger_of_ready,
                            "slow"  : target_station.slow_charger_of_ready
                        }
                    },
                    "chargers_in_station" : [{
                        "id"               : charger.id,
                        "index_in_station" : charger.index_in_station,
                        "output"           : charger.output,
                        "method"           : charger.method,
                        "charger_type"     : charger.charger_type.explanation,
                        "charging_status"  : charger.charging_status.explanation
                    } for charger in station.charger_set.all()]
                } for target_station in target_stations if target_station == station]
            } for station in near_stations]

            return JsonResponse({"results" : results}, status=200)

        except KeyError:
            return JsonResponse({"MESSAGE" : "KEY_ERROR"}, status=400)
        
        except ValidationError as error:
            return JsonResponse({"MESSAGE": error.message}, status=error.code)


class SearchNearestEVView(View):
    def get(self, request):
        category = Category.STATION.value

        user_latitude  = float(request.GET.get("user_latitude", None))
        user_longitude = float(request.GET.get("user_longitude", None)) 
        user_position  = (user_latitude, user_longitude)

        search_position_latitude, search_position_longitude = validate_search_position(user_latitude, user_longitude, category)

        nearest_station = True
        range           = 0

        while nearest_station:
            range += 1
            search_range = (
                    Q(latitude__range  = (search_position_latitude - Length.LATITUDE_100m.value * range, search_position_latitude + Length.LATITUDE_100m.value * range)) &
                    Q(longitude__range = (search_position_longitude - Length.LONGITUDE_100m.value * range, search_position_longitude + Length.LONGITUDE_100m.value * range))
                )

            stations = Station.objects.filter(search_range)
            
            distances = [haversine(user_position, (station.latitude, station.longitude)) for station in stations]
            if distances:
                break

        nearest_distance = min(distances)
        nearest_station  = stations[distances.index(nearest_distance)]

        results = {
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
            .filter(regions)\
            .annotate(total_station=Count("station", distinct=True))\
            .annotate(total_charger=Count("station__charger"))\
            .annotate(communication_abnomal_charger=Count("station__charger__charging_status", Case(When(station__charger__charging_status=ChargingStatus.COMMUNICATION_ABNOMAL.value, then=True))))\
            .annotate(ready_charger=Count("station__charger__charging_status", Case(When(station__charger__charging_status=ChargingStatus.READY.value, then=True))))\
            .annotate(charging_charger=Count("station__charger__charging_status", Case(When(station__charger__charging_status=ChargingStatus.CHARGING.value, then=True))))\
            .annotate(suspending_charger=Count("station__charger__charging_status", Case(When(station__charger__charging_status=ChargingStatus.SUSPENDING.value, then=True))))\
            .annotate(inspecting_charger=Count("station__charger__charging_status", Case(When(station__charger__charging_status=ChargingStatus.INSPECTING.value, then=True))))\
            .annotate(not_confirmed_charger=Count("station__charger__charging_status", Case(When(station__charger__charging_status=ChargingStatus.NOT_CONFIRMED.value, then=True))))

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