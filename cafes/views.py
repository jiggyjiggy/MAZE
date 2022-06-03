from django.http      import JsonResponse
from django.views     import View
from django.db.models import Q

from cafes.models import Cafe


class CafeMapView(View):
    def get(self, request):
        SW_latitude  = float(request.GET.get("SW_latitude", None))
        SW_longitude = float(request.GET.get("SW_longitude", None)) 
        NE_latitude  = float(request.GET.get("NE_latitude", None))
        NE_longitude = float(request.GET.get("NE_longitude", None))

        rectangle_boundary = (
                Q(latitude__range  = (SW_latitude, NE_latitude)) &
                Q(longitude__range = (SW_longitude, NE_longitude))
            )
        
        near_cafes = Cafe.objects.filter(rectangle_boundary)

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