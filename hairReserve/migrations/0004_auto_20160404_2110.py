# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0003_auto_20160404_1726'),
    ]

    operations = [
        migrations.AddField(
            model_name='barbershop',
            name='description',
            field=models.CharField(max_length=430, blank=True),
        ),
        migrations.AddField(
            model_name='barbershop',
            name='end_date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='barbershop',
            name='operation_end_time',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='barbershop',
            name='operation_start_time',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='barbershop',
            name='rating',
            field=models.DecimalField(default=0, max_digits=2, decimal_places=1),
        ),
        migrations.AddField(
            model_name='barbershop',
            name='start_date',
            field=models.DateField(null=True),
        ),
    ]
