# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-07 12:52
from __future__ import unicode_literals

from django.db import migrations


def migrate_data_to_external_app(apps, schema_editor):
    FroidePage = apps.get_model('document', 'Page')
    FCPage = apps.get_model('filingcabinet', 'Page')

    for page in FroidePage.objects.all():
        FCPage.objects.create(
            id=page.id,
            document_id=page.document_id,
            number=page.number,
            content=page.content,
            image=page.image,
            image_large=page.image_large,
            image_normal=page.image_normal,
            image_small=page.image_small
        )

    FroidePageAnnotation = apps.get_model('document', 'PageAnnotation')
    FCPageAnnotation = apps.get_model('filingcabinet', 'PageAnnotation')

    for anno in FroidePageAnnotation.objects.all():
        FCPageAnnotation.objects.create(
            id=anno.id,
            page_id=anno.page_id,
            title=anno.title,
            description=anno.description,
            user_id=anno.user_id,
            top=anno.top,
            left=anno.left,
            width=anno.width,
            height=anno.height,
            image=anno.image
        )


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0007_auto_20180807_1448'),
    ]

    operations = [
        migrations.RunPython(migrate_data_to_external_app),
    ]
