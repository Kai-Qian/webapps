# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0004_auto_20160404_2110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='barbershop',
            name='operation_end_time',
            field=models.CharField(default=b'0000', max_length=10, blank=True),
        ),
        migrations.AlterField(
            model_name='barbershop',
            name='operation_start_time',
            field=models.CharField(default=b'0000', max_length=10, blank=True),
        ),
    ]
