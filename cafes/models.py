from django.db import models
from core.models import TimeStampModel


class Cafe(TimeStampModel):
    land_lot_number_address = models.CharField(max_length=100)
    road_name_address       = models.CharField(max_length=100)
    name                    = models.CharField(max_length=50)
    latitude                = models.DecimalField(max_digits=17, decimal_places=14)
    longitude               = models.DecimalField(max_digits=17, decimal_places=14)
    category                = models.ForeignKey("commons.Category", on_delete=models.PROTECT)
    zcode                   = models.ForeignKey("commons.Region", on_delete=models.PROTECT)

    class Meta:
        db_table = "cafes"