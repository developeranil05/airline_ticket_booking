from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Flight, Seat, Booking, MonitoringUser, AdminUser
from django.contrib.auth.models import User

def monitoring_login_new(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            monitoring_user = MonitoringUser.objects.get(
                username=username,
                is_active=True
            )
            
            if monitoring_user.check_password(password):
                monitoring_user.update_last_login()
                request.session['monitoring_user_id'] = monitoring_user.id
                request.session['monitoring_username'] = username
                
                messages.success(request, 'Welcome to monitoring dashboard')
                return redirect('monitoring-dashboard-new')
            else:
                messages.error(request, 'Invalid password')
        except MonitoringUser.DoesNotExist:
            messages.error(request, 'Invalid username or account not found')
    
    return render(request, 'monitoring/login.html')

def monitoring_required_new(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('monitoring_user_id'):
            return redirect('monitoring-login-new')
        
        try:
            monitoring_user = MonitoringUser.objects.get(
                id=request.session['monitoring_user_id'],
                is_active=True
            )
            request.monitoring_user = monitoring_user
        except MonitoringUser.DoesNotExist:
            request.session.flush()
            return redirect('monitoring-login-new')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@monitoring_required_new
def monitoring_dashboard_new(request):
    # Get all data
    total_users = User.objects.count()
    total_monitoring_users = MonitoringUser.objects.filter(is_active=True).count()
    
    all_flights = Flight.objects.all()
    all_seats = Seat.objects.all()
    all_bookings = Booking.objects.all()
    
    stats = {
        'total_users': total_users,
        'total_monitoring_users': total_monitoring_users,
        'total_flights': all_flights.count(),
        'active_flights': all_flights.filter(is_active=True).count(),
        'total_seats': all_seats.count(),
        'booked_seats': all_seats.filter(is_booked=True).count(),
        'available_seats': all_seats.filter(is_booked=False).count(),
        'total_bookings': all_bookings.count(),
        'confirmed_bookings': all_bookings.filter(state='CONFIRMED').count(),
        'pending_bookings': all_bookings.filter(state='SEAT_HELD').count(),
        'cancelled_bookings': all_bookings.filter(state='CANCELLED').count(),
    }
    
    users = User.objects.all().order_by('-date_joined')[:20]
    monitoring_users = MonitoringUser.objects.all().order_by('-created_date')
    flights = Flight.objects.all().order_by('-created_at')[:20]
    bookings = Booking.objects.all().order_by('-created_at')[:20]
    
    return render(request, 'monitoring/dashboard_new.html', {
        'stats': stats,
        'monitoring_user': request.monitoring_user,
        'monitoring_users': monitoring_users,
        'recent_flights': all_flights.order_by('-created_at')[:10],
        'recent_bookings': all_bookings.order_by('-created_at')[:10],
        'users': users,
        'flights': flights,
        'bookings': bookings,
    })

def monitoring_logout_new(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('monitoring-login-new')