# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-22 16:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0021_auto_20160322_1637'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='state',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
    ]
