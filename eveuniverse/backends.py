from celery_once import AlreadyQueued
from django.core.cache import cache


class DjangoBackend:
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
