import hashlib
import json

from enum import Enum

from django.http  import JsonResponse
from django.views import View

from commons.models import Region, Category
from evs.models     import ChargingStatus, Charger


class ChargerType_(Enum):
    DC_CHAdeMO = 1
    AC_SLOW    = 2
    DC_COMBO   = 4
    AC_3SANG   = 7

filtering_include_search = [
        {"title" : "DC차데모", "nums" : "1,3,5,6"},
        {"title" : "AC완속", "nums" : "2"},
        {"title" : "DC콤보", "nums" : "4,5,6"},
        {"title" : "AC3상", "nums" : "3,6,7"}
    ]


class ParentTableView(View):
    def get(self, request):
        regions          = Region.objects.all()
        categories       = Category.objects.all()
        charger_statuses = ChargingStatus.objects.all()
        chargers         = Charger.objects.values("output").order_by("output").distinct()

        results = {
            "regions" : [{ 
                "city" : region.city
            } for region in regions],
            "categories" : [{
                "type": category.type
            } for category in categories],
            "charger": {
                "filtering_include_search" : filtering_include_search,
                "statuses":[{
                    "explanation" : charger_status.explanation
                } for charger_status in charger_statuses],
                "outputs" : {
                    "output" : [{
                        "query"    : charger["output"],
                        "capacity" : str(charger["output"]) + "kw" 
                    } for charger in chargers if charger["output"] != None]}
                }
            }

        If_None_Match = request.META.get("HTTP_IF_NONE_MATCH", None)
        ETag_hash     = hashlib.md5(json.dumps({"results" : results}).encode('utf-8')).hexdigest()
        if  If_None_Match == ETag_hash:
            return JsonResponse({"MESSAGE" : "NOT_MODIFIED"}, status=304)

        return JsonResponse({"results" : results}, status=200)