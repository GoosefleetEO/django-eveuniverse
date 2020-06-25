# Generated by Django 2.2.13 on 2020-06-25 16:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('eveuniverse', '0007_auto_20200625_1246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eveancestry',
            name='eve_bloodline',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_bloodlines', to='eveuniverse.EveBloodline'),
        ),
        migrations.AlterField(
            model_name='eveasteroidbelt',
            name='eve_planet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_asteroid_belts', to='eveuniverse.EvePlanet'),
        ),
        migrations.AlterField(
            model_name='evebloodline',
            name='eve_race',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='eve_bloodlines', to='eveuniverse.EveRace'),
        ),
        migrations.AlterField(
            model_name='evebloodline',
            name='eve_ship_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_bloodlines', to='eveuniverse.EveType'),
        ),
        migrations.AlterField(
            model_name='eveconstellation',
            name='eve_region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_constellations', to='eveuniverse.EveRegion'),
        ),
        migrations.AlterField(
            model_name='evedogmaattribute',
            name='eve_unit',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='eve_units', to='eveuniverse.EveUnit'),
        ),
        migrations.AlterField(
            model_name='evedogmaeffect',
            name='duration_attribute',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='duration_attributes', to='eveuniverse.EveDogmaAttribute'),
        ),
        migrations.AlterField(
            model_name='evefaction',
            name='eve_solar_system',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='eve_solar_systems', to='eveuniverse.EveSolarSystem'),
        ),
        migrations.AlterField(
            model_name='evegroup',
            name='eve_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_groups', to='eveuniverse.EveCategory'),
        ),
        migrations.AlterField(
            model_name='evemarketgroup',
            name='parent_market_group',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='sub_market_groups', to='eveuniverse.EveMarketGroup'),
        ),
        migrations.AlterField(
            model_name='evemoon',
            name='eve_planet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_moons', to='eveuniverse.EvePlanet'),
        ),
        migrations.AlterField(
            model_name='eveplanet',
            name='eve_solar_system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_planets', to='eveuniverse.EveSolarSystem'),
        ),
        migrations.AlterField(
            model_name='eveplanet',
            name='eve_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_planets', to='eveuniverse.EveType'),
        ),
        migrations.AlterField(
            model_name='evesolarsystem',
            name='eve_constellation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_solarsystems', to='eveuniverse.EveConstellation'),
        ),
        migrations.AlterField(
            model_name='evesolarsystem',
            name='eve_star',
            field=models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='eve_solarsystem', to='eveuniverse.EveStar'),
        ),
        migrations.AlterField(
            model_name='evestar',
            name='eve_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_stars', to='eveuniverse.EveType'),
        ),
        migrations.AlterField(
            model_name='evestargate',
            name='eve_solar_system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_stargates', to='eveuniverse.EveSolarSystem'),
        ),
        migrations.AlterField(
            model_name='evestargate',
            name='eve_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_stargates', to='eveuniverse.EveType'),
        ),
        migrations.AlterField(
            model_name='evestation',
            name='eve_race',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='eve_stations', to='eveuniverse.EveRace'),
        ),
        migrations.AlterField(
            model_name='evestation',
            name='eve_solar_system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_stations', to='eveuniverse.EveSolarSystem'),
        ),
        migrations.AlterField(
            model_name='evestation',
            name='eve_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_stations', to='eveuniverse.EveType'),
        ),
        migrations.AlterField(
            model_name='evetype',
            name='eve_graphic',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='eve_types', to='eveuniverse.EveGraphic'),
        ),
        migrations.AlterField(
            model_name='evetype',
            name='eve_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_types', to='eveuniverse.EveGroup'),
        ),
        migrations.AlterField(
            model_name='evetype',
            name='eve_market_group',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='eve_types', to='eveuniverse.EveMarketGroup'),
        ),
        migrations.AlterField(
            model_name='evetypedogmaattribute',
            name='eve_dogma_attribute',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_type_dogma_attributes', to='eveuniverse.EveDogmaAttribute'),
        ),
        migrations.AlterField(
            model_name='evetypedogmaeffect',
            name='eve_dogma_effect',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eve_type_dogma_effects', to='eveuniverse.EveDogmaEffect'),
        ),
    ]