# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0012_barbershop_total_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='barbershop',
            name='total_rating',
            field=models.DecimalField(default=0, max_digits=5, decimal_places=1),
        ),
    ]
