from enum import Enum

from django.db   import models

from core.models import TimeStampModel


class ChargingStatus(Enum):
    communication_abnomal = 1
    ready                 = 2
    charging              = 3
    suspending            = 4
    inspecting            = 5
    not_confirmed         = 9


class Station(TimeStampModel):

    class YesOrNo(models.TextChoices):
        YES = "Y"
        NO  = "N"

    id                        = models.CharField(primary_key=True, max_length=20)
    name                      = models.CharField(max_length=100)
    detail_location           = models.CharField(max_length=100, null=True)
    road_name_address         = models.CharField(max_length=100, null=True)
    latitude                  = models.DecimalField(max_digits=17, decimal_places=14)
    longitude                 = models.DecimalField(max_digits=17, decimal_places=14)
    hours_of_operation        = models.CharField(max_length=100, blank=True)
    business_id               = models.CharField(max_length=10, db_index=True)
    business_name             = models.CharField(max_length=30)
    business_manamgement_name = models.CharField(max_length=30)
    business_call             = models.CharField(max_length=30, null=True)
    parking_free_yes_or_no    = models.CharField(max_length=1, choices=YesOrNo.choices, blank=True)
    parking_detail            = models.CharField(max_length=200, blank=True)
    limit_yes_or_no           = models.CharField(max_length=1, choices=YesOrNo.choices, blank=True)
    limit_detail              = models.CharField(max_length=200, blank=True)
    delete_yes_or_no          = models.CharField(max_length=1, choices=YesOrNo.choices, blank=True)
    delete_detail             = models.CharField(max_length=200, blank=True)
    category                  = models.ForeignKey("commons.Category", on_delete=models.PROTECT)
    region                    = models.ForeignKey("commons.Region", on_delete=models.PROTECT)

    class Meta:
        db_table = "stations"


class Charger(models.Model):
    index_in_station = models.PositiveSmallIntegerField()
    output           = models.PositiveSmallIntegerField(blank=True, null=True)
    method           = models.CharField(max_length=10, blank=True)
    charger_type     = models.ForeignKey("ChargerType", on_delete=models.PROTECT)
    station          = models.ForeignKey("Station", on_delete=models.CASCADE)
    charging_status  = models.ForeignKey("ChargingStatus", on_delete=models.PROTECT, default=ChargingStatus.not_confirmed.value)

    class Meta:
        db_table = "chargers"


class ChargerHistory(TimeStampModel):
    charger_status_update_datetime = models.DateTimeField(null=True)
    last_charging_start_datetime   = models.DateTimeField(null=True)
    last_charging_end_datetime     = models.DateTimeField(null=True)
    now_charging_start_datetime    = models.DateTimeField(null=True)
    charging_status                = models.ForeignKey("ChargingStatus", on_delete=models.PROTECT, default=ChargingStatus.not_confirmed.value)
    charger                        = models.ForeignKey("Charger", on_delete=models.CASCADE)

    class Meta:
        db_table = "charger_histories"


class ChargerType(models.Model):
    code        = models.PositiveSmallIntegerField(primary_key=True)
    explanation = models.CharField(max_length=50)

    class Meta:
        db_table = "charger_types"


class ChargingStatus(models.Model):
    code        = models.PositiveSmallIntegerField(primary_key=True)
    explanation = models.CharField(max_length=10)

    class Meta:
        db_table = "charging_statuses"