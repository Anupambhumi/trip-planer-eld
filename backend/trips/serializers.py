from rest_framework import serializers
from .models import Trip


class LogHeaderSerializer(serializers.Serializer):
    driver_name = serializers.CharField(required=False, allow_blank=True, default="")
    co_driver_name = serializers.CharField(required=False, allow_blank=True, default="")
    carrier_name = serializers.CharField(required=False, allow_blank=True, default="")
    main_office_address = serializers.CharField(required=False, allow_blank=True, default="")
    home_terminal_address = serializers.CharField(required=False, allow_blank=True, default="")
    truck_number = serializers.CharField(required=False, allow_blank=True, default="")
    trailer_number = serializers.CharField(required=False, allow_blank=True, default="")
    shipping_doc = serializers.CharField(required=False, allow_blank=True, default="")
    shipper_commodity = serializers.CharField(required=False, allow_blank=True, default="")


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used_hours = serializers.FloatField(min_value=0, max_value=70)
    start_datetime = serializers.DateTimeField(required=False)
    log_header = LogHeaderSerializer(required=False)


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"


class TripListSerializer(serializers.ModelSerializer):
    """Lightweight list view — omits the heavy `result` payload."""
    class Meta:
        model = Trip
        fields = (
            "id", "current_location", "pickup_location", "dropoff_location",
            "current_cycle_used_hours", "driver_name", "carrier_name",
            "total_miles", "total_drive_hours", "num_days", "created_at",
        )
