import redis

r = redis.from_url("redis://localhost:6379/1")
deleted_count = 0
if keys := r.keys(":?:qo_eveuniverse.*"):
    print(f"We found {len(keys)} locks for eveuniverse tasks.")
    response = input("Delete (y/N)?")
    if response.lower() == "y":
        deleted_count += r.delete(*keys)
        print(f"Deleted {deleted_count} celery once keys.")
else:
    print("No locks found.")
