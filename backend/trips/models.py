from django.db import models


class Trip(models.Model):
    """Stores each planned trip so results can be retrieved later."""
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_used_hours = models.FloatField(default=0)

    # Optional log-header info
    driver_name = models.CharField(max_length=120, blank=True, default="")
    co_driver_name = models.CharField(max_length=120, blank=True, default="")
    carrier_name = models.CharField(max_length=160, blank=True, default="")
    main_office_address = models.CharField(max_length=255, blank=True, default="")
    truck_number = models.CharField(max_length=60, blank=True, default="")
    trailer_number = models.CharField(max_length=60, blank=True, default="")

    total_miles = models.FloatField(null=True, blank=True)
    total_drive_hours = models.FloatField(null=True, blank=True)
    num_days = models.IntegerField(null=True, blank=True)

    result = models.JSONField(null=True, blank=True)  # full planner payload
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pickup_location} -> {self.dropoff_location}"
