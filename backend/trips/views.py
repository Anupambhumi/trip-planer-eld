from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import TripInputSerializer
from .services.planner import plan_trip
from .services.geo import GeoError, suggest_cities
from .repository import get_repository


@api_view(["GET"])
def geocode_suggest(request):
    """Autocomplete: return US city suggestions for `?q=`."""
    query = request.query_params.get("q", "")
    try:
        return Response(suggest_cities(query))
    except Exception:  # pragma: no cover - suggestions are best-effort
        return Response([])


@api_view(["GET"])
def health(request):
    repo = get_repository()
    return Response({
        "status": "ok",
        "service": "trippilot-ai",
        "storage": repo.backend,
    })


@api_view(["POST"])
def plan(request):
    """Plan a trip: geocode + route + build HOS-compliant daily logs."""
    serializer = TripInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    header = dict(data.get("log_header") or {})
    try:
        result = plan_trip(
            current=data["current_location"],
            pickup=data["pickup_location"],
            dropoff=data["dropoff_location"],
            cycle_used_hours=data["current_cycle_used_hours"],
            start_dt=data.get("start_datetime"),
            log_header=header,
        )
    except GeoError as exc:
        return Response({"error": str(exc)},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as exc:  # pragma: no cover - safety net
        return Response({"error": f"Unexpected error: {exc}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    doc = {
        "current_location": result["inputs"]["current_location"],
        "pickup_location": result["inputs"]["pickup_location"],
        "dropoff_location": result["inputs"]["dropoff_location"],
        "current_cycle_used_hours": data["current_cycle_used_hours"],
        "driver_name": header.get("driver_name", ""),
        "co_driver_name": header.get("co_driver_name", ""),
        "carrier_name": header.get("carrier_name", ""),
        "main_office_address": header.get("main_office_address", ""),
        "truck_number": header.get("truck_number", ""),
        "trailer_number": header.get("trailer_number", ""),
        "total_miles": result["summary"]["total_miles"],
        "total_drive_hours": result["summary"]["total_drive_hours"],
        "num_days": result["summary"]["num_days"],
        "result": result,
    }
    trip_id = get_repository().save(doc)
    result["trip_id"] = trip_id
    return Response(result, status=status.HTTP_200_OK)


@api_view(["GET"])
def trip_detail(request, pk):
    result = get_repository().get(pk)
    if result is None:
        return Response({"error": "Trip not found"},
                        status=status.HTTP_404_NOT_FOUND)
    return Response(result)


@api_view(["GET"])
def trip_list(request):
    return Response(get_repository().list(limit=50))
