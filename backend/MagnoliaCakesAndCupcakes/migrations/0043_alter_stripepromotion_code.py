# Generated by Django 4.2.4 on 2023-10-06 05:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MagnoliaCakesAndCupcakes', '0042_alter_stripepromotion_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stripepromotion',
            name='code',
            field=models.CharField(blank=True, max_length=50, primary_key=True, serialize=False, unique=True),
        ),
    ]
