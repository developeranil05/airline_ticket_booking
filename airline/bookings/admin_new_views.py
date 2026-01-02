from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Flight, Seat, Booking, AdminUser
from django.contrib.auth.models import User

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            admin_user = AdminUser.objects.get(
                admin_name=username,
                is_active=True
            )
            
            if admin_user.check_password(password):
                admin_user.update_last_login()
                request.session['admin_user_id'] = admin_user.id
                request.session['admin_username'] = username
                request.session['admin_airline'] = admin_user.airline_code
                
                messages.success(request, f'Welcome to {admin_user.airline_name} admin dashboard')
                return redirect('admin-dashboard-new')
            else:
                messages.error(request, 'Invalid password')
        except AdminUser.DoesNotExist:
            messages.error(request, 'Invalid username or account not found')
    
    return render(request, 'admin/login.html')

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_user_id'):
            return redirect('admin-login-new')
        
        try:
            admin_user = AdminUser.objects.get(
                id=request.session['admin_user_id'],
                is_active=True
            )
            request.admin_user = admin_user
        except AdminUser.DoesNotExist:
            request.session.flush()
            return redirect('admin-login-new')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def admin_dashboard_new(request):
    airline_code = request.session.get('admin_airline')
    
    # Filter flights by airline code (assuming flight codes start with airline code)
    airline_flights = Flight.objects.filter(code__startswith=airline_code)
    airline_seats = Seat.objects.filter(flight__code__startswith=airline_code)
    airline_bookings = Booking.objects.filter(seat__flight__code__startswith=airline_code)
    
    stats = {
        'airline_name': request.admin_user.airline_name,
        'total_flights': airline_flights.count(),
        'active_flights': airline_flights.filter(is_active=True).count(),
        'total_seats': airline_seats.count(),
        'booked_seats': airline_seats.filter(is_booked=True).count(),
        'available_seats': airline_seats.filter(is_booked=False).count(),
        'total_bookings': airline_bookings.count(),
        'confirmed_bookings': airline_bookings.filter(state='CONFIRMED').count(),
        'pending_bookings': airline_bookings.filter(state='SEAT_HELD').count(),
        'cancelled_bookings': airline_bookings.filter(state='CANCELLED').count(),
    }
    
    return render(request, 'admin/dashboard_new.html', {
        'stats': stats,
        'admin_user': request.admin_user,
        'recent_flights': airline_flights.order_by('-created_at')[:5],
        'recent_bookings': airline_bookings.order_by('-created_at')[:5]
    })

@admin_required
def admin_flights_new(request):
    airline_code = request.session.get('admin_airline')
    flights = Flight.objects.filter(code__startswith=airline_code).order_by('-departure_time')
    
    return render(request, 'admin/flights_new.html', {
        'flights': flights,
        'admin_user': request.admin_user
    })

def admin_logout_new(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('admin-login-new')