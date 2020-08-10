# Operations Guide

## Installation

To install django-eveuniverse into your Django project please follow the these steps:

### Install from PyPI

You can install this app directly from PyPI:

```bash
pip install django-eveuniverse
```

### Update settings

Next add `eveuniverse` to `INSTALLED_APPS` in your project's settings file.

By default only the core models are automatically loaded on-demand. If you want to also include some of the additional models please add them to your settings. (See also  [settings](#settings) for a list of all available settings)

### Setup celery

This app uses celery for loading large sets of data, e.g. with the load commands. Please make sure celery is setup and working for your Django project.

```eval_rst
.. note::
    Note on celery worker setup

    For an efficient loading of large amounts of data from ESI we recommend a thread based setup of celery workers with at least 10 concurrent workers.

    For example on our test system with 20 gevent threads the loading of the complete Eve Online map (with the command: **eveuniverse_load_data map**) consisting of all regions, constellation and solar systems took only about 5 minutes.
```

### Finalize installation

```bash
python manage.py migrate
```

Finally restart your Django instance so your changes become effective.

## Updating

```eval_rst
.. hint::
    Before updating please always check the `Change Log <https://gitlab.com/ErikKalkoken/django-eveuniverse/-/blob/master/CHANGELOG.md>`_ for any special instructions on updating or important changes that might affect your project.
```

To update your installation first install the new version:

```bash
pip install django-eveuniverse
```

Then run Django migrations:

```bash
python manage.py migrate
```

And finally restart your Django instance so your changes become effective.

## Settings

Here is a list of available settings for this app. They can be configured by adding them to your local Django settings file.

Most settings will enable the automatic loading of related models. Note that this will exponentially increase load times of objects, so we recommend to only enable additional models that are functionally needed. For example: if you enable Planets, all related planet object are automatically loaded when updating a solar system.

```eval_rst
    .. |br| raw:: html

        <br>

    .. list-table:: Settings

        *   - Name
            - Description
            - Default
        *   - `EVEUNIVERSE_LOAD_ASTEROID_BELTS`
            - When true will automatically load |br| astroid belts with every planet
            - `False`
        *   - `EVEUNIVERSE_LOAD_DOGMAS`
            - When true will automatically load |br| dogma, e.g. with every type
            - `False`
        *   - `EVEUNIVERSE_LOAD_GRAPHICS`
            - When true will automatically load |br| graphics with every type
            - `False`
        *   - `EVEUNIVERSE_LOAD_MARKET_GROUPS`
            - When true will automatically load |br| market groups with every type
            - `False`
        *   - `EVEUNIVERSE_LOAD_MOONS`
            - When true will automatically load |br| moons be with every planet
            - `False`
        *   - `EVEUNIVERSE_LOAD_PLANETS`
            - When true will automatically load |br| planets with every solar system
            - `False`
        *   - `EVEUNIVERSE_LOAD_STARGATES`
            - When true will automatically load |br| planets with every solar system
            - `False`
        *   - `EVEUNIVERSE_LOAD_STARS`
            - When true will automatically load |br| stars with every solar system
            - `False`
        *   - `EVEUNIVERSE_LOAD_STATIONS`
            - When true will automatically load |br| stations be with every solar system
            - `False`
```

Note that all settings are optional and the app will use the documented default settings if they are not used.

## Management commands

The following management commands are available:

- **eveuniverse_load_data**: This command will load a complete set of data form ESI and store it locally. Useful to optimize performance or when you want to provide the user with drop-down lists. Available sets:
  - **map**: All regions, constellations and solar systems
  - **ships**: All ship types
  - **structures**: All structures types
- **eveuniverse_purge_all**: This command will purge ALL data of your models.
- **eveuniverse_load_type**: This command can load a specific set of types. This is a helper command meant to be called from other apps only.

## Database tools

On some DBMS like MySQL it is not possible to reset the database and remove all eveuniverse tables with the standard "migrate zero" command. The reason is that eveuniverse is using composite primary keys and Django seams to have problems dealing with that correctly, when trying to roll back migrations.

As workaround you will need remove all tables with SQL commands. To make this easier we are providing a SQL script that contains all commands to drop the tables. The full process for "migrating to zero" is as follows:

1. Run SQL script `drop_tables.sql` on your database
2. Run `python manage.py migrate eveuniverse zero --fake`