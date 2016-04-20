# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0008_auto_20160405_2218'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservations',
            name='barbershop',
        ),
        migrations.AddField(
            model_name='reservations',
            name='barbershop',
            field=models.ForeignKey(related_name='reservations', to='hairReserve.Barbershop', null=True),
        ),
    ]
