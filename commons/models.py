from django.db import models


class Category(models.Model):
    type = models.CharField(max_length=10)
       
    class Meta:
        db_table = "categories"


class Region(models.Model):
    zcode = models.PositiveSmallIntegerField(primary_key=True)
    city  = models.CharField(max_length=10)

    class Meta:
        db_table = "regions"