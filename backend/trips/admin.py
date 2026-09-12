from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "pickup_location", "dropoff_location",
                    "total_miles", "num_days", "created_at")
    search_fields = ("pickup_location", "dropoff_location")
