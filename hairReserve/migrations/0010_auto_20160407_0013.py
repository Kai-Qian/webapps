# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0009_auto_20160405_2221'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservations',
            name='end_time',
            field=models.CharField(default=b'00:00', max_length=10, blank=True),
        ),
        migrations.AlterField(
            model_name='reservations',
            name='start_time',
            field=models.CharField(default=b'00:00', max_length=10, blank=True),
        ),
    ]
