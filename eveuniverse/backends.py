"""Backend for Celery Once."""

from celery_once import AlreadyQueued
from django.core.cache import cache


class DjangoBackend:
    """A celery once backend.

    This is a general purpose backend, which should work with many different
    Django installations.

    However, it uses Django's cache for locking and is therefore not guaranteed to be
    thread safe. This depends on which cache backend is used and how it is implemented.

    If in doubt and when possible we recommend using celery once's redis backend.
    """

    def __init__(self, settings):
        pass

    @staticmethod
    def raise_or_lock(key, timeout):
        acquired = cache.add(key=key, value="lock", timeout=timeout)
        if not acquired:
            raise AlreadyQueued(int(cache.ttl(key)))

    @staticmethod
    def clear_lock(key):
        return cache.delete(key)
