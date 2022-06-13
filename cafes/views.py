from haversine import haversine

from django.http      import JsonResponse
from django.views     import View
from django.db.models import Q, Prefetch

from cafes.models import Cafe

from core.utils import query_debugger


class CafeMapView(View):
    @query_debugger
    def get(self, request):
        SW_latitude  = float(request.GET["SW_latitude"])
        SW_longitude = float(request.GET["SW_longitude"]) 
        NE_latitude  = float(request.GET["NE_latitude"])
        NE_longitude = float(request.GET["NE_longitude"])

        rectangle_boundary = (
                Q(latitude__range  = (SW_latitude, NE_latitude)) &
                Q(longitude__range = (SW_longitude, NE_longitude))
            )
        
        near_cafes = Cafe.objects\
            .select_related("category", "region")\
            .filter(rectangle_boundary)

        results = [{
            "land_lot_number_address" : near_cafe.land_lot_number_address,
            "road_name_address"       : near_cafe.road_name_address,
            "name"                    : near_cafe.name,
            "latitude"                : near_cafe.latitude,
            "longitude"               : near_cafe.longitude,
            "category"                : near_cafe.category.type,
            "region"                  : near_cafe.region.city
        } for near_cafe in near_cafes]

        return JsonResponse({"results" : results}, status=200)


class SearchNearestCafeView(View):
    @query_debugger
    def get(self, request):
        # 1 degree of longitude = 111.19 km
        # 1 degree of latitude in seoul (longitude: 37 degree) = 88.80 km
        LATITUDE_100m  = 0.0008993614533681087 
        LONGITUDE_100m = 0.0011261261261261261

        user_latitude  = float(request.GET.get("user_latitude", None))
        user_longitude = float(request.GET.get("user_longitude", None)) 
        user_position  = (user_latitude, user_longitude)

        nearest_cafe = True
        offset       = 0

        while nearest_cafe:
            offset += 1
            search_range = (
                    Q(latitude__range  = (user_latitude - LATITUDE_100m * offset, user_latitude + LATITUDE_100m * offset)) &
                    Q(longitude__range = (user_longitude - LONGITUDE_100m * offset, user_longitude + LONGITUDE_100m * offset))
                )

            cafes = Cafe.objects.filter(search_range)
            
            distances = [haversine(user_position, (cafe.latitude, cafe.longitude)) for cafe in cafes]
            if distances:
                break

        nearest_distance = min(distances)
        nearest_cafe     = cafes[distances.index(nearest_distance)]

        results = {
            "search_range" : {
                "km" : 0.1 * offset
            },
            "nearest_cafe" : {
                    "km"        : nearest_distance,
                    "id"        : nearest_cafe.id,
                    "latitude"  : nearest_cafe.latitude,
                    "longitude" : nearest_cafe.longitude
                }
            }

        return JsonResponse({"results" : results}, status=200)