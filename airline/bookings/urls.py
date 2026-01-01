from django.urls import path
from .views import (
    FlightListCreateView,
    FlightDetailView,
    BookingCreateView,
    BookingListView,
    PaymentView,
    CancelView,
    RefundView,
    SeatListCreateView,
)
from .template_views import (
    flight_list,
    flight_seats,
    book_seat,
    booking_list,
    booking_detail,
    process_booking_payment,
    cancel_booking_view,
)


urlpatterns = [
    # API Endpoints
    path("api/seats/", SeatListCreateView.as_view(), name="seat-list-create"),
    path("api/flights/", FlightListCreateView.as_view(), name="flight-list-create"),
    path("api/flights/<int:pk>/", FlightDetailView.as_view(), name="flight-detail"),
    path("api/bookings/", BookingListView.as_view(), name="booking-list"),
    path("api/book/", BookingCreateView.as_view(), name="booking-create"),
    path("api/bookings/<int:pk>/pay/", PaymentView.as_view(), name="booking-payment"),
    path("api/bookings/<int:pk>/cancel/", CancelView.as_view(), name="booking-cancel"),
    path("api/bookings/<int:pk>/refund/", RefundView.as_view(), name="booking-refund"),
    
    # GUI Endpoints
    path("", flight_list, name="flight-list-gui"),
    path("flights/<int:flight_id>/seats/", flight_seats, name="flight-seats-gui"),
    path("book/<int:seat_id>/", book_seat, name="book-seat-gui"),
    path("my-bookings/", booking_list, name="booking-list-gui"),
    path("booking/<int:booking_id>/", booking_detail, name="booking-detail-gui"),
    path("booking/<int:booking_id>/pay/", process_booking_payment, name="process-payment-gui"),
    path("booking/<int:booking_id>/cancel/", cancel_booking_view, name="cancel-booking-gui"),
]

