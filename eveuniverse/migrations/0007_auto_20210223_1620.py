# Generated by Django 3.1.6 on 2021-02-23 16:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("eveuniverse", "0006_evetype_sections_loaded"),
    ]

    operations = [
        migrations.RenameField(
            model_name="evetype",
            old_name="sections_loaded",
            new_name="enabled_sections",
        ),
    ]
