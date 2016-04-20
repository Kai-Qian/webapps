# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0011_barbershop_number_of_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='barbershop',
            name='total_rating',
            field=models.DecimalField(default=0, max_digits=10, decimal_places=1),
        ),
    ]
