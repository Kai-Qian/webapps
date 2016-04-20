# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0002_auto_20160323_1634'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='reservation',
        ),
        migrations.AddField(
            model_name='barbershop',
            name='service_type',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='reservations',
            name='endTime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='reservations',
            name='startTime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='reservations',
            name='type',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.DeleteModel(
            name='Service',
        ),
    ]
