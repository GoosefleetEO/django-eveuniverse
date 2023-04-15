# Generated by Django 3.1.1 on 2020-10-23 13:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("eveuniverse", "0002_load_eveunit"),
    ]

    operations = [
        migrations.CreateModel(
            name="EveMarketPrice",
            fields=[
                (
                    "eve_type",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="market_price",
                        serialize=False,
                        to="eveuniverse.evetype",
                    ),
                ),
                ("adjusted_price", models.FloatField(default=None, null=True)),
                ("average_price", models.FloatField(default=None, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
            ],
        ),
    ]
