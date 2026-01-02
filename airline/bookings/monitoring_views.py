from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import Flight, Seat, Booking, MonitoringUser, AdminUser
from django.contrib.auth.models import User
from django.db.models import Count
import logging

logger = logging.getLogger('bookings')

def monitoring_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            monitoring_user = MonitoringUser.objects.get(
                username=username,
                is_active=True
            )
            
            if monitoring_user.check_password(password):
                # Update last login
                monitoring_user.update_last_login()
                
                # Store in session
                request.session['monitoring_user_id'] = monitoring_user.id
                request.session['monitoring_username'] = username
                
                messages.success(request, f'Welcome to monitoring dashboard')
                return redirect('monitoring-dashboard')
            else:
                messages.error(request, 'Invalid password')
        except MonitoringUser.DoesNotExist:
            messages.error(request, 'Invalid username or account not found')
    
    return render(request, 'monitoring/login.html')

def monitoring_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('monitoring_user_id'):
            return redirect('monitoring-login')
        
        try:
            monitoring_user = MonitoringUser.objects.get(
                id=request.session['monitoring_user_id'],
                is_active=True
            )
            request.monitoring_user = monitoring_user
        except MonitoringUser.DoesNotExist:
            request.session.flush()
            return redirect('monitoring-login')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@monitoring_required
def monitoring_dashboard(request):
    print("*** MONITORING DASHBOARD VIEW CALLED ***")
    # System-wide statistics - ALL data from ALL tables
    total_users = User.objects.count()
    total_monitoring_users = MonitoringUser.objects.filter(is_active=True).count()
    
    # All flights and bookings (no filtering)
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
        'refunded_bookings': all_bookings.filter(state='REFUNDED').count(),
    }
    
    # Get all data for tabs
    users = User.objects.all().order_by('-date_joined')[:20]
    monitoring_users = MonitoringUser.objects.all().order_by('-created_date')
    
    # Get admin users with flight counts
    admin_users_data = []
    for admin_user in AdminUser.objects.all().order_by('-created_date'):
        flight_count = Flight.objects.filter(airline_code=admin_user.airline_code).count()
        admin_users_data.append({
            'admin': admin_user,
            'flight_count': flight_count,
            'username': admin_user.admin_name,
            'password': admin_user.actual_password,
            'phone': admin_user.phone_number,
        })
    
    flights = Flight.objects.all().order_by('-created_at')[:20]
    seats = Seat.objects.all().order_by('-created_at')[:50]
    bookings = Booking.objects.all().order_by('-created_at')[:20]
    
    return render(request, 'monitoring/dashboard.html', {
        'stats': stats,
        'monitoring_user': request.monitoring_user,
        'monitoring_users': monitoring_users,
        'recent_flights': all_flights.order_by('-created_at')[:10],
        'recent_bookings': all_bookings.order_by('-created_at')[:10],
        'users': users,
        'admin_users_data': admin_users_data,
        'flights': flights,
        'seats': seats,
        'bookings': bookings,
    })

@monitoring_required
def monitoring_flights(request):
    # Show ALL flights from ALL airlines
    flights = Flight.objects.all().order_by('-departure_time')
    
    return render(request, 'monitoring/flights.html', {
        'flights': flights,
        'monitoring_user': request.monitoring_user
    })

@monitoring_required
def monitoring_bookings(request):
    # Show ALL bookings from ALL airlines
    bookings = Booking.objects.all().select_related('seat__flight', 'created_by').order_by('-created_at')
    
    return render(request, 'monitoring/bookings.html', {
        'bookings': bookings,
        'monitoring_user': request.monitoring_user
    })

@monitoring_required
def toggle_flight_status(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    
    flight.is_active = not flight.is_active
    flight.save()
    
    return JsonResponse({
        'success': True,
        'is_active': flight.is_active,
        'message': f'Flight {flight.code} {"activated" if flight.is_active else "deactivated"}'
    })

@monitoring_required
def add_monitoring_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        is_active = request.POST.get('is_active') == 'on'
        
        if not all([username, password, first_name, last_name]):
            return JsonResponse({'success': False, 'message': 'All fields are required'})
        
        if MonitoringUser.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'})
        
        try:
            user = MonitoringUser.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active
            )
            user.set_password(password)
            user.save()
            return JsonResponse({'success': True, 'message': f'Monitoring user {username} created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error creating user: {str(e)}'})
    
    return render(request, 'monitoring/add_user.html', {
        'monitoring_user': request.monitoring_user
    })

@monitoring_required
def monitoring_tables(request):
    # Get data from all tables
    users = User.objects.all().order_by('-date_joined')[:20]
    monitoring_users = MonitoringUser.objects.all().order_by('-created_date')
    
    # Get admin users with flight counts
    admin_users_data = []
    for admin_user in AdminUser.objects.all().order_by('-created_date'):
        flight_count = Flight.objects.filter(airline_code=admin_user.airline_code).count()
        admin_users_data.append({
            'admin': admin_user,
            'flight_count': flight_count,
            'username': admin_user.admin_name,
            'password': admin_user.actual_password,  # Show actual password
            'phone': admin_user.phone_number,
        })
    
    flights = Flight.objects.all().order_by('-created_at')[:20]
    seats = Seat.objects.all().order_by('-created_at')[:50]
    bookings = Booking.objects.all().order_by('-created_at')[:20]
    
    return render(request, 'monitoring/tables.html', {
        'users': users,
        'monitoring_users': monitoring_users,
        'admin_users_data': admin_users_data,
        'flights': flights,
        'seats': seats,
        'bookings': bookings,
        'monitoring_user': request.monitoring_user
    })

@monitoring_required
def update_admin_user(request, user_id):
    if request.method == 'POST':
        try:
            admin_user = get_object_or_404(AdminUser, id=user_id)
            admin_user.admin_name = request.POST.get('admin_name', admin_user.admin_name)
            admin_user.email = request.POST.get('email', admin_user.email)
            admin_user.phone_number = request.POST.get('phone_number', admin_user.phone_number)
            
            # Update actual password if provided
            new_password = request.POST.get('actual_password')
            if new_password:
                admin_user.actual_password = new_password
                admin_user.set_password(new_password)
            
            admin_user.is_active = request.POST.get('is_active') == 'on'
            admin_user.save()
            return JsonResponse({'success': True, 'message': 'Admin user updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error updating admin user: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@monitoring_required
def delete_admin_user(request, user_id):
    if request.method == 'POST':
        try:
            admin_user = get_object_or_404(AdminUser, id=user_id)
            username = admin_user.admin_name
            admin_user.delete()
            return JsonResponse({'success': True, 'message': f'Admin user {username} deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error deleting admin user: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@monitoring_required
def update_monitoring_user(request, user_id):
    if request.method == 'POST':
        try:
            monitoring_user = get_object_or_404(MonitoringUser, id=user_id)
            new_username = request.POST.get('username', monitoring_user.username)
            
            # Check if username is being changed and if it already exists
            if new_username != monitoring_user.username and MonitoringUser.objects.filter(username=new_username).exists():
                return JsonResponse({'success': False, 'message': 'Username already exists'})
            
            monitoring_user.username = new_username
            monitoring_user.first_name = request.POST.get('first_name', monitoring_user.first_name)
            monitoring_user.last_name = request.POST.get('last_name', monitoring_user.last_name)
            monitoring_user.is_active = request.POST.get('is_active') == 'on'
            monitoring_user.save()
            return JsonResponse({'success': True, 'message': 'Monitoring user updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error updating monitoring user: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@monitoring_required
def delete_monitoring_user(request, user_id):
    if request.method == 'POST':
        try:
            monitoring_user = get_object_or_404(MonitoringUser, id=user_id)
            username = monitoring_user.username
            monitoring_user.delete()
            return JsonResponse({'success': True, 'message': f'Monitoring user {username} deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error deleting monitoring user: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@monitoring_required
def update_system_user(request, user_id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            new_username = request.POST.get('username', user.username)
            
            # Check if username is being changed and if it already exists
            if new_username != user.username and User.objects.filter(username=new_username).exists():
                return JsonResponse({'success': False, 'message': 'Username already exists'})
            
            user.username = new_username
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.is_staff = request.POST.get('is_staff') == 'on'
            user.is_active = request.POST.get('is_active') == 'on'
            
            # Update password if provided
            new_password = request.POST.get('password')
            if new_password:
                user.set_password(new_password)
            
            user.save()
            return JsonResponse({'success': True, 'message': 'System user updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error updating system user: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@monitoring_required
def delete_system_user(request, user_id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            username = user.username
            user.delete()
            return JsonResponse({'success': True, 'message': f'System user {username} deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error deleting system user: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@monitoring_required
def add_admin_user(request):
    if request.method == 'POST':
        admin_name = request.POST.get('admin_name')
        airline_code = request.POST.get('airline_code')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        actual_password = request.POST.get('actual_password')
        is_active = request.POST.get('is_active') == 'on'
        
        if not all([admin_name, airline_code, email, phone_number, actual_password]):
            return JsonResponse({'success': False, 'message': 'All fields are required'})
        
        # Get airline name from choices
        airline_choices = dict(AdminUser.AIRLINE_CHOICES)
        airline_name = airline_choices.get(airline_code, 'Unknown')
        
        try:
            admin_user = AdminUser.objects.create(
                admin_name=admin_name,
                airline_code=airline_code,
                airline_name=airline_name,
                email=email,
                phone_number=phone_number,
                actual_password=actual_password,
                is_active=is_active
            )
            admin_user.set_password(actual_password)
            admin_user.save()
            return JsonResponse({'success': True, 'message': f'Admin user {admin_name} created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error creating admin user: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@monitoring_required
def add_system_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        if not all([username, first_name, last_name, email, password]):
            return JsonResponse({'success': False, 'message': 'All fields are required'})
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'})
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists'})
        
        try:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                is_staff=is_staff,
                is_active=is_active
            )
            return JsonResponse({'success': True, 'message': f'System user {username} created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error creating system user: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def monitoring_logout(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('monitoring-login')