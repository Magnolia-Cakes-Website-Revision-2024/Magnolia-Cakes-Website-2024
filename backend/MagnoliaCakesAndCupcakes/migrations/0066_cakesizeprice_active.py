# Generated by Django 4.2.4 on 2023-10-16 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MagnoliaCakesAndCupcakes', '0065_rename_cake_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='cakesizeprice',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
