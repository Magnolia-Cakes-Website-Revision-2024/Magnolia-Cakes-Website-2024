# Generated by Django 4.2.4 on 2023-10-06 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MagnoliaCakesAndCupcakes', '0043_alter_stripepromotion_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripepromotion',
            name='onlyLoggedInUsers',
            field=models.BooleanField(default=False),
        ),
    ]
