# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0010_auto_20160407_0013'),
    ]

    operations = [
        migrations.AddField(
            model_name='barbershop',
            name='number_of_comments',
            field=models.IntegerField(default=0),
        ),
    ]
