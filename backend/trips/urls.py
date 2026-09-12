from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("plan/", views.plan, name="plan"),
    path("geocode/suggest/", views.geocode_suggest, name="geocode-suggest"),
    path("trips/", views.trip_list, name="trip-list"),
    path("trips/<str:pk>/", views.trip_detail, name="trip-detail"),
]
