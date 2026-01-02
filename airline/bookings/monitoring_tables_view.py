@monitoring_required
def monitoring_tables(request):
    # Get data from all tables
    users = User.objects.all().order_by('-date_joined')[:20]
    monitoring_users = MonitoringUser.objects.all().order_by('-created_date')
    flights = Flight.objects.all().order_by('-created_at')[:20]
    seats = Seat.objects.all().order_by('-created_at')[:50]
    bookings = Booking.objects.all().order_by('-created_at')[:20]
    
    return render(request, 'monitoring/tables.html', {
        'users': users,
        'monitoring_users': monitoring_users,
        'flights': flights,
        'seats': seats,
        'bookings': bookings,
        'monitoring_user': request.monitoring_user
    })