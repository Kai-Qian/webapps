# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hairReserve', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='country',
        ),
        migrations.RemoveField(
            model_name='address',
            name='line1Address',
        ),
        migrations.RemoveField(
            model_name='barbershop',
            name='url',
        ),
        migrations.AddField(
            model_name='address',
            name='address',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='address',
            name='user',
            field=models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='barbershop',
            name='picture_url',
            field=models.CharField(max_length=256, blank=True),
        ),
        migrations.AddField(
            model_name='barbershop',
            name='website',
            field=models.CharField(max_length=765, blank=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='city',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='state',
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='zip',
            field=models.CharField(max_length=10, blank=True),
        ),
        migrations.AlterField(
            model_name='barbershop',
            name='phone',
            field=models.CharField(blank=True, max_length=15, validators=[django.core.validators.RegexValidator(regex=b'^\\+?1?\\d{9,15}$', message=b"Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")]),
        ),
    ]
