# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0006_remove_reservations_endtime'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reservations',
            old_name='dateAndTime',
            new_name='reservation_date_and_time',
        ),
        migrations.RenameField(
            model_name='reservations',
            old_name='type',
            new_name='service_type',
        ),
        migrations.RemoveField(
            model_name='reservations',
            name='startTime',
        ),
        migrations.AddField(
            model_name='reservations',
            name='star_time',
            field=models.CharField(default=b'0000', max_length=10, blank=True),
        ),
        migrations.AddField(
            model_name='reservations',
            name='start_date',
            field=models.DateField(null=True),
        ),
    ]
