# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0014_auto_20160417_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='barbershop',
            name='operation_end_time',
            field=models.CharField(default=b'0000', max_length=10),
        ),
        migrations.AlterField(
            model_name='barbershop',
            name='operation_start_time',
            field=models.CharField(default=b'0000', max_length=10),
        ),
        migrations.AlterField(
            model_name='barbershop',
            name='phone',
            field=models.CharField(max_length=15, validators=[django.core.validators.RegexValidator(regex=b'^\\+?1?\\d{9,15}$', message=b"Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")]),
        ),
        migrations.AlterField(
            model_name='barbershop',
            name='service_type',
            field=models.CharField(max_length=200),
        ),
    ]
