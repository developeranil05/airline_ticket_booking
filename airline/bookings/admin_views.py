from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Flight, Seat, Booking
from django.contrib.auth.models import User
import logging

logger = logging.getLogger('bookings')

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('flight-list-gui')
        
    stats = {
        'total_flights': Flight.objects.count(),
        'total_bookings': Booking.objects.count(),
        'confirmed_bookings': Booking.objects.filter(state='CONFIRMED').count(),
        'pending_refunds': Booking.objects.filter(state='CANCELLED', refund_processed=False).count(),
    }
    return render(request, 'admin/dashboard.html', {'stats': stats})

@login_required
def manage_flights(request):
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('flight-list-gui')
        
    flights = Flight.objects.select_related('created_by').order_by('-created_at')[:50]
    return render(request, 'admin/manage_flights.html', {'flights': flights})

@login_required
def add_flight(request):
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('flight-list-gui')
        
    if request.method == 'POST':
        try:
            flight = Flight.objects.create(
                code=request.POST.get('code'),
                departure_time=request.POST.get('departure_time'),
                arrival_time=request.POST.get('arrival_time'),
                origin=request.POST.get('origin'),
                destination=request.POST.get('destination'),
                price=request.POST.get('price'),
                aircraft_type=request.POST.get('aircraft_type', 'Boeing 737'),
                total_seats=int(request.POST.get('total_seats', 180)),
                created_by=request.user
            )
            
            # Create seats for the flight
            create_seats_for_flight(flight)
            
            messages.success(request, f'Flight {flight.code} added successfully!')
            return redirect('manage-flights')
        except Exception as e:
            messages.error(request, f'Error adding flight: {str(e)}')
            logger.error(f"Flight creation error: {str(e)}")
    
    return render(request, 'admin/add_flight.html')

def create_seats_for_flight(flight):
    """Create seats for a flight (6 seats per row: A,B,C,D,E,F)"""
    rows = flight.total_seats // 6
    for row in range(1, rows + 1):
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            Seat.objects.create(
                flight=flight,
                seat_number=f"{row}{letter}",
                row_number=row,
                seat_letter=letter,
                is_window=(letter in ['A', 'F']),
                is_aisle=(letter in ['C', 'D']),
                created_by=flight.created_by
            )

@login_required
def pending_refunds(request):
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('flight-list-gui')
        
    bookings = Booking.objects.select_related(
        'seat__flight', 'created_by'
    ).filter(
        state='CANCELLED', 
        refund_processed=False
    ).order_by('-cancelled_date')[:50]
    return render(request, 'admin/pending_refunds.html', {'bookings': bookings})