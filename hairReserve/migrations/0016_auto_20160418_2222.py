# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0015_auto_20160418_2220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservations',
            name='end_time',
            field=models.CharField(default=b'00:00', max_length=10),
        ),
        migrations.AlterField(
            model_name='reservations',
            name='start_time',
            field=models.CharField(default=b'00:00', max_length=10),
        ),
    ]
