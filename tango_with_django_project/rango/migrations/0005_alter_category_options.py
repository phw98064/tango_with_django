# Generated by Django 3.2.5 on 2021-07-29 22:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rango', '0004_alter_category_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'Categories'},
        ),
    ]
