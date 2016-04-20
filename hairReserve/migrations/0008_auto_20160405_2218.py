# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0007_auto_20160405_2056'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reservations',
            old_name='star_time',
            new_name='start_time',
        ),
    ]
