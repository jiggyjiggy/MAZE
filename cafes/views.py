from enum import Enum

from haversine import haversine

from django.http            import JsonResponse
from django.views           import View
from django.core.exceptions import ValidationError
from django.db.models       import Q

from cafes.models     import Cafe
from core.validations import validate_range, validate_search_position


class Length(Enum):
    # 1 degree of longitude = 111.19 km
    # 1 degree of latitude in seoul (longitude: 37 degree) = 88.80 km
    LATITUDE_100m  = 0.0008993614533681087 
    LONGITUDE_100m = 0.0011261261261261261


class Category(Enum):
    STATION = 1
    CAFE    = 2


class CafeMapView(View):
    def get(self, request):
        try:
            SW_latitude  = float(request.GET["SW_latitude"])
            SW_longitude = float(request.GET["SW_longitude"]) 
            NE_latitude  = float(request.GET["NE_latitude"])
            NE_longitude = float(request.GET["NE_longitude"])

            # validate_range(NE_latitude, SW_latitude, NE_longitude, SW_longitude)  # 프론트 이슈(첫 렌더시 range 벗어남)

            rectangle_boundary = (
                    Q(latitude__range  = (SW_latitude, NE_latitude)) &
                    Q(longitude__range = (SW_longitude, NE_longitude))
                )
            
            near_cafes = Cafe.objects\
                .select_related("category", "region")\
                .filter(rectangle_boundary)

            results = [{
                "id"                      : near_cafe.id,
                "land_lot_number_address" : near_cafe.land_lot_number_address,
                "road_name_address"       : near_cafe.road_name_address,
                "name"                    : near_cafe.name,
                "latitude"                : near_cafe.latitude,
                "longitude"               : near_cafe.longitude,
                "category"                : near_cafe.category.type,
                "region"                  : near_cafe.region.city
            } for near_cafe in near_cafes]

            return JsonResponse({"results" : results}, status=200)

        except KeyError:
            return JsonResponse({"MESSAGE" : "KEY_ERROR"}, status=400)
        
        except ValidationError as error:
            return JsonResponse({"MESSAGE": error.message}, status=error.code)


class SearchNearestCafeView(View):
    def get(self, request):
        category = Category.CAFE.value

        user_latitude  = float(request.GET.get("user_latitude", None))
        user_longitude = float(request.GET.get("user_longitude", None)) 
        user_position  = (user_latitude, user_longitude)

        search_position_latitude, search_position_longitude = validate_search_position(user_latitude, user_longitude, category)

        nearest_cafe = True
        range        = 0

        while nearest_cafe:
            range += 1
            search_range = (
                    Q(latitude__range  = (search_position_latitude - Length.LATITUDE_100m.value * range, search_position_latitude + Length.LATITUDE_100m.value * range)) &
                    Q(longitude__range = (search_position_longitude - Length.LONGITUDE_100m.value * range, search_position_longitude + Length.LONGITUDE_100m.value * range))
                )

            cafes = Cafe.objects.filter(search_range)
            
            distances = [haversine(user_position, (cafe.latitude, cafe.longitude)) for cafe in cafes]
            if distances:
                break

        nearest_distance = min(distances)
        nearest_cafe     = cafes[distances.index(nearest_distance)]

        results = {
            "nearest_cafe" : {
                    "km"        : nearest_distance,
                    "id"        : nearest_cafe.id,
                    "name"      : nearest_cafe.name,
                    "latitude"  : nearest_cafe.latitude,
                    "longitude" : nearest_cafe.longitude
                }
            }

        return JsonResponse({"results" : results}, status=200)