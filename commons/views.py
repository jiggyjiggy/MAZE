import hashlib
import json

from enum import Enum

from django.http  import JsonResponse
from django.views import View

from commons.models import Region, Category
from evs.models     import ChargerType, ChargingStatus, Charger


def include_charger_types():
    charger_types    = ChargerType.objects.all()

    filtering_include_search = []
    for charger_type in charger_types:
        if charger_type.code in [ChargerType_.DC_CHAdeMO.value, ChargerType_.AC_SLOW.value,ChargerType_.DC_COMBO.value,ChargerType_.AC_3SANG.value]:
            charger_type_code_list = []
            for compare_target in charger_types:
                if charger_type.explanation in compare_target.explanation:
                    charger_type_code_list.append(str(compare_target.code))
            
            nums = ','.join(charger_type_code_list)
            filtering_include_search.append({"title" : charger_type.explanation, "nums":nums})

    return filtering_include_search


class ChargerType_(Enum):
    DC_CHAdeMO = 1
    AC_SLOW    = 2
    DC_COMBO   = 4
    AC_3SANG   = 7


class Usable(Enum):
    YES = "YES"
    NO  = "NO"


class ParentTableView(View):
    def get(self, request):
        regions          = Region.objects.all()
        categories       = Category.objects.all()
        charger_statuses = ChargingStatus.objects.all()
        chargers         = Charger.objects.values("output").order_by("output").distinct()

        filtering_include_search = include_charger_types()

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
                            "capacity" : str(charger["output"]) + "kw",
                            "query"    : charger["output"]
                        } for charger in chargers if charger["output"] != None]
                    },
                    "usable" : { 
                        "title" : "사용가능한 충전기 보기",
                        "query" : Usable.YES.value
                    }
                },
            }
    
        If_None_Match = request.META.get("HTTP_IF_NONE_MATCH", None)
        ETag_hash     = hashlib.md5(json.dumps({"results" : results}).encode('utf-8')).hexdigest()
        if  If_None_Match == ETag_hash:
            return JsonResponse({"MESSAGE" : "NOT_MODIFIED"}, status=304)

        return JsonResponse({"results" : results}, status=200)