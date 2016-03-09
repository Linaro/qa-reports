# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-04 13:31
from __future__ import unicode_literals

from django.db import migrations


def migrate(apps, schema_editor):
    Model = apps.get_model("reports", "TestJob")

    for item in Model.objects.all():
        if item.run_definition:
            item.kind = item.run_definition.definition.kind
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_testjob_kind'),
    ]

    operations = [
        migrations.RunPython(migrate, migrations.RunPython.noop)
    ]
