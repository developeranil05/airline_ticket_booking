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
    payment_page,
    process_booking_payment,
    cancel_booking_view,
    process_refund_view,
    edit_passenger,
    delete_booking,
    change_passengers,
)
from .monitoring_views import (
    monitoring_login,
    monitoring_dashboard,
    monitoring_flights,
    monitoring_bookings,
    monitoring_tables,
    add_monitoring_user,
    toggle_flight_status,
    monitoring_logout,
    update_admin_user,
    delete_admin_user,
    update_monitoring_user,
    delete_monitoring_user,
    update_system_user,
    delete_system_user,
    add_admin_user,
    add_system_user,
)
from . import admin_views
from .admin_new_views import (
    admin_login,
    admin_dashboard_new,
    admin_flights_new,
    admin_logout_new,
)
from .monitoring_new_views import (
    monitoring_login_new,
    monitoring_dashboard_new,
    monitoring_logout_new,
)
from .test_views import test_monitoring
from .api_autocomplete import city_suggestions


urlpatterns = [
    # API Endpoints
    path("api/cities/", city_suggestions, name="city-suggestions"),
    path("api/seats/", SeatListCreateView.as_view(), name="seat-list-create"),
    path("api/flights/", FlightListCreateView.as_view(), name="flight-list-create"),
    path("api/flights/<int:pk>/", FlightDetailView.as_view(), name="flight-detail"),
    path("api/bookings/", BookingListView.as_view(), name="booking-list"),
    path("api/book/", BookingCreateView.as_view(), name="booking-create"),
    path("api/bookings/<int:pk>/pay/", PaymentView.as_view(), name="booking-payment"),
    path("api/bookings/<int:pk>/cancel/", CancelView.as_view(), name="booking-cancel"),
    path("api/bookings/<int:pk>/refund/", RefundView.as_view(), name="booking-refund"),
    
    # Admin URLs
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin-dashboard'),
    path('admin-flights/', admin_views.manage_flights, name='manage-flights'),
    path('admin-flights-add/', admin_views.add_flight, name='add-flight'),
    path('admin-refunds/', admin_views.pending_refunds, name='pending-refunds'),
    
    # New Admin URLs
    path('admin-new/', admin_login, name='admin-login-new'),
    path('admin-new/dashboard/', admin_dashboard_new, name='admin-dashboard-new'),
    path('admin-new/flights/', admin_flights_new, name='admin-flights-new'),
    path('admin-new/logout/', admin_logout_new, name='admin-logout-new'),
    
    # GUI Endpoints
    path("", flight_list, name="flight-list-gui"),
    path("flights/<int:flight_id>/seats/", flight_seats, name="flight-seats-gui"),
    path("book/<int:seat_id>/", book_seat, name="book-seat-gui"),
    path("my-bookings/", booking_list, name="booking-list-gui"),
    path("booking/<int:booking_id>/", booking_detail, name="booking-detail-gui"),
    path("booking/<int:booking_id>/payment/", payment_page, name="payment-page-gui"),
    path("booking/<int:booking_id>/pay/", process_booking_payment, name="process-payment-gui"),
    path("booking/<int:booking_id>/cancel/", cancel_booking_view, name="cancel-booking-gui"),
    path("booking/<int:booking_id>/refund/", process_refund_view, name="process-refund-gui"),
    path("booking/<int:booking_id>/edit/", edit_passenger, name="edit-passenger-gui"),
    path("booking/<int:booking_id>/delete/", delete_booking, name="delete-booking-gui"),
    path("booking/<int:booking_id>/change-passengers/", change_passengers, name="change-passengers-gui"),
    
    # Test URL
    path('test-monitoring/', test_monitoring, name='test-monitoring'),
    
    # New Monitoring URLs
    path('monitoring-new/', monitoring_login_new, name='monitoring-login-new'),
    path('monitoring-new/dashboard/', monitoring_dashboard_new, name='monitoring-dashboard-new'),
    path('monitoring-new/logout/', monitoring_logout_new, name='monitoring-logout-new'),
    
    # Monitoring URLs
    path('monitoring/', monitoring_login, name='monitoring-login'),
    path('monitoring/dashboard/', monitoring_dashboard, name='monitoring-dashboard'),
    path('monitoring/flights/', monitoring_flights, name='monitoring-flights'),
    path('monitoring/bookings/', monitoring_bookings, name='monitoring-bookings'),
    path('monitoring/tables/', monitoring_tables, name='monitoring-tables'),
    path('monitoring/add-user/', add_monitoring_user, name='add-monitoring-user'),
    path('monitoring/toggle-flight/<int:flight_id>/', toggle_flight_status, name='toggle-flight-status'),
    path('monitoring/logout/', monitoring_logout, name='monitoring-logout'),
    
    # Monitoring CRUD URLs
    path('monitoring/admin-user/<int:user_id>/update/', update_admin_user, name='update-admin-user'),
    path('monitoring/admin-user/<int:user_id>/delete/', delete_admin_user, name='delete-admin-user'),
    path('monitoring/monitoring-user/<int:user_id>/update/', update_monitoring_user, name='update-monitoring-user'),
    path('monitoring/monitoring-user/<int:user_id>/delete/', delete_monitoring_user, name='delete-monitoring-user'),
    path('monitoring/system-user/<int:user_id>/update/', update_system_user, name='update-system-user'),
    path('monitoring/system-user/<int:user_id>/delete/', delete_system_user, name='delete-system-user'),
    path('monitoring/add-admin-user/', add_admin_user, name='add-admin-user'),
    path('monitoring/add-system-user/', add_system_user, name='add-system-user'),
]

