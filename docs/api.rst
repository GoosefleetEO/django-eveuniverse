.. currentmodule:: eveuniverse

===============
API
===============

This chapter contains the developer reference documentation of the public API for *django-eveuniverse* consisting of all models, their manager methods and helpers.

.. _api-eve-models:

Core functions
==============

dotlan
----------------
.. automodule:: eveuniverse.core.dotlan
    :members:

esitools
----------------
.. automodule:: eveuniverse.core.esitools
    :members:

eveimageserver
----------------
.. automodule:: eveuniverse.core.eveimageserver
    :members:

eveitems
----------------
.. automodule:: eveuniverse.core.eveitems
    :members:

evemicros
----------------
.. automodule:: eveuniverse.core.evemicros
    :members:

evesdeapi
----------------
.. automodule:: eveuniverse.core.evesdeapi
    :members:

eveskinserver
----------------
.. automodule:: eveuniverse.core.eveskinserver
    :members:

evewho
----------------
.. automodule:: eveuniverse.core.evewho
    :members:

evexml
---------------
.. automodule:: eveuniverse.core.evexml
    :members:

zkillboard
---------------
.. automodule:: eveuniverse.core.zkillboard
    :members:

Eve Models
==========

.. automodule:: eveuniverse.models
    :members:

.. _api-manager-methods:

Manager methods
====================

Default manager methods
-------------------------

All eve models have the following manager methods:

.. autoclass:: eveuniverse.managers.EveUniverseEntityModelManager
    :members:

.. _api-managers-eve-entity:

EveEntity manager methods
-------------------------

EveEntity comes with some additional manager methods.

.. autoclass:: eveuniverse.managers.EveEntityQuerySet
    :members:

.. autoclass:: eveuniverse.managers.EveEntityManager
    :members: get_or_create_esi, update_or_create_esi, bulk_create_esi, bulk_update_new_esi, bulk_update_all_esi, resolve_name, bulk_resolve_names, fetch_by_names_esi

Other manager methods
-------------------------

.. autoclass:: eveuniverse.managers.EveMarketPriceManager
    :members:

Helpers
====================

.. autoclass:: eveuniverse.helpers.EveEntityNameResolver
    :members: to_name

.. autofunction:: eveuniverse.helpers.meters_to_au

.. autofunction:: eveuniverse.helpers.meters_to_ly

Tasks
====================

Eve Universe tasks
------------------

.. autofunction:: eveuniverse.tasks.load_eve_object

.. autofunction:: eveuniverse.tasks.update_or_create_eve_object

EveEntity tasks
---------------

.. autofunction:: eveuniverse.tasks.create_eve_entities

.. autofunction:: eveuniverse.tasks.update_unresolved_eve_entities

Object loader tasks
-------------------

.. autofunction:: eveuniverse.tasks.create_eve_entities
    :noindex:

.. autofunction:: eveuniverse.tasks.update_unresolved_eve_entities
    :noindex:

.. autofunction:: eveuniverse.tasks.load_map

.. autofunction:: eveuniverse.tasks.load_all_types

.. autofunction:: eveuniverse.tasks.load_eve_types


Other tasks
-------------------

.. autofunction:: eveuniverse.tasks.update_market_prices

Tools
====================

Testdata
-------------------

.. automodule:: eveuniverse.tools.testdata
    :members:

.. seealso::
    Please also see :ref:`developer-testdata` on how to create test data for your app.
