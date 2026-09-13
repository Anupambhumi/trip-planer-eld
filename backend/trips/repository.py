"""
Trip persistence layer.

Primary store is MongoDB (via pymongo). If ``MONGODB_URI`` is unset or the
server can't be reached, we transparently fall back to Django's ORM (SQLite)
so the app always runs. Views only ever talk to ``get_repository()``.
"""

from datetime import datetime, timezone

from django.conf import settings

LIGHT_FIELDS = (
    "current_location", "pickup_location", "dropoff_location",
    "current_cycle_used_hours", "driver_name", "carrier_name",
    "total_miles", "total_drive_hours", "num_days",
)


def _now():
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
class MongoTripRepository:
    backend = "mongodb"

    def __init__(self, client):
        self.client = client
        db = client[settings.MONGODB_DB_NAME]
        self.col = db[settings.MONGODB_COLLECTION]
        self.col.create_index("created_at")

    def save(self, doc):
        doc = {**doc, "created_at": _now()}
        res = self.col.insert_one(doc)
        return str(res.inserted_id)

    def get(self, trip_id):
        from bson import ObjectId
        from bson.errors import InvalidId
        try:
            oid = ObjectId(trip_id)
        except (InvalidId, TypeError):
            return None
        doc = self.col.find_one({"_id": oid})
        if not doc:
            return None
        result = doc.get("result") or {}
        result["trip_id"] = str(doc["_id"])
        return result

    def list(self, limit=50):
        cursor = self.col.find(
            {}, projection={"result": 0}).sort("created_at", -1).limit(limit)
        out = []
        for doc in cursor:
            item = {field: doc.get(field) for field in LIGHT_FIELDS}
            item["id"] = str(doc["_id"])
            created = doc.get("created_at")
            item["created_at"] = created.isoformat() if created else None
            out.append(item)
        return out


# --------------------------------------------------------------------------
class OrmTripRepository:
    backend = "sqlite-orm"

    def save(self, doc):
        from .models import Trip
        trip = Trip.objects.create(
            current_location=doc["current_location"],
            pickup_location=doc["pickup_location"],
            dropoff_location=doc["dropoff_location"],
            current_cycle_used_hours=doc["current_cycle_used_hours"],
            driver_name=doc.get("driver_name", ""),
            co_driver_name=doc.get("co_driver_name", ""),
            carrier_name=doc.get("carrier_name", ""),
            main_office_address=doc.get("main_office_address", ""),
            truck_number=doc.get("truck_number", ""),
            trailer_number=doc.get("trailer_number", ""),
            total_miles=doc["total_miles"],
            total_drive_hours=doc["total_drive_hours"],
            num_days=doc["num_days"],
            result=doc["result"],
        )
        return str(trip.id)

    def get(self, trip_id):
        from .models import Trip
        try:
            trip = Trip.objects.get(pk=int(trip_id))
        except (Trip.DoesNotExist, ValueError, TypeError):
            return None
        result = trip.result or {}
        result["trip_id"] = str(trip.id)
        return result

    def list(self, limit=50):
        from .models import Trip
        out = []
        for trip in Trip.objects.all()[:limit]:
            item = {field: getattr(trip, field) for field in LIGHT_FIELDS}
            item["id"] = str(trip.id)
            item["created_at"] = trip.created_at.isoformat()
            out.append(item)
        return out


# --------------------------------------------------------------------------
_repo = None
_mongo_client = None


def _try_mongo():
    """Return a connected pymongo client, or None if unavailable."""
    global _mongo_client
    if not settings.MONGODB_URI:
        return None
    if _mongo_client is not None:
        return _mongo_client
    try:
        from pymongo import MongoClient
        client = MongoClient(settings.MONGODB_URI,
                             serverSelectionTimeoutMS=2500)
        client.admin.command("ping")   # forces a real connection check
        _mongo_client = client
        return client
    except Exception:
        return None


def _ensure_orm_schema():
    """Create the trips table if this host skipped migrate (common on Render)."""
    from django.core.management import call_command
    from django.db import connection
    if "trips_trip" not in connection.introspection.table_names():
        call_command("migrate", interactive=False, verbosity=0)


def get_repository():
    """Pick MongoDB if reachable, otherwise the ORM. Cached after first call."""
    global _repo
    if _repo is not None:
        return _repo
    client = _try_mongo()
    if client:
        _repo = MongoTripRepository(client)
        return _repo
    _ensure_orm_schema()
    _repo = OrmTripRepository()
    return _repo


def reset_repository():
    """Testing helper — clears the cached repository/client."""
    global _repo, _mongo_client
    _repo = None
    _mongo_client = None
