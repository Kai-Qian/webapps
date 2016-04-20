# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hairReserve', '0016_auto_20160418_2222'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='primaryCity',
            new_name='primary_city',
        ),
    ]
