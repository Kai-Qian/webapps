# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0005_auto_20160405_0347'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservations',
            name='endTime',
        ),
    ]
