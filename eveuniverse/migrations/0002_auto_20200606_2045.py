# Generated by Django 2.2.13 on 2020-06-06 20:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("eveuniverse", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EveTypeDogmaEffects",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("effect_id", models.PositiveIntegerField(db_index=True)),
                ("is_default", models.BooleanField()),
                (
                    "eve_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="eveuniverse.EveType",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EveTypeDogmaAttributes",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("attribute_id", models.PositiveIntegerField(db_index=True)),
                ("value", models.FloatField()),
                (
                    "eve_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="eveuniverse.EveType",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EveStargateDestination",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "eve_solar_system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="eveuniverse.EveSolarSystem",
                    ),
                ),
                (
                    "eve_stargate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="eveuniverse.EveStargate",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="evetypedogmaeffects",
            constraint=models.UniqueConstraint(
                fields=("eve_type", "effect_id"), name="functional PK"
            ),
        ),
        migrations.AddConstraint(
            model_name="evetypedogmaattributes",
            constraint=models.UniqueConstraint(
                fields=("eve_type", "attribute_id"), name="functional PK"
            ),
        ),
        migrations.AddConstraint(
            model_name="evestargatedestination",
            constraint=models.UniqueConstraint(
                fields=("eve_stargate", "eve_solar_system"), name="functional PK"
            ),
        ),
    ]
