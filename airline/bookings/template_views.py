from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from .models import Flight, Seat, Booking
from .services import create_booking, process_payment, cancel_booking, refund_booking
from .exceptions import SeatNotAvailableError, BookingError, InvalidStateTransitionError, PaymentError
from django.contrib.auth.models import User
from django.contrib.auth import login
import logging

logger = logging.getLogger('bookings')

def flight_list(request):
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    date = request.GET.get('date', '')
    passengers = request.GET.get('passengers', '1')
    
    flights = Flight.objects.filter(is_active=True)
    
    if origin:
        flights = flights.filter(origin__icontains=origin)
    if destination:
        flights = flights.filter(destination__icontains=destination)
    if date:
        flights = flights.filter(departure_time__date=date)
    
    flights = flights.order_by('departure_time')[:20]
    
    # Add seat statistics
    for flight in flights:
        total_seats = flight.seats.count()
        booked_seats = flight.seats.filter(is_booked=True).count()
        available_seats = total_seats - booked_seats
        
        flight.total_seats_count = total_seats
        flight.booked_seats_count = booked_seats
        flight.available_seats_count = available_seats
    
    return render(request, 'bookings/flight_list.html', {
        'flights': flights,
        'origin': origin,
        'destination': destination,
        'date': date,
        'passengers': passengers
    })

def flight_seats(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    
    # Optimized query with select_related and prefetch_related
    seats = flight.seats.select_related('flight').order_by('row_number', 'seat_letter')
    
    # Get held seats efficiently
    from django.utils import timezone
    held_seat_ids = set(Booking.objects.filter(
        seat__flight_id=flight_id,
        state__in=['SEAT_HELD', 'PAYMENT_PENDING'],
        seat_hold_until__gt=timezone.now()
    ).values_list('seat_id', flat=True))
    
    # Add held status efficiently
    for seat in seats:
        seat.is_held = seat.id in held_seat_ids
    
    # Calculate seat statistics
    total_seats = seats.count()
    booked_seats = seats.filter(is_booked=True).count()
    held_seats = len(held_seat_ids)
    available_seats = total_seats - booked_seats - held_seats
    
    return render(request, 'bookings/flight_seats.html', {
        'flight': flight,
        'seats': seats,
        'total_seats': total_seats,
        'booked_seats': booked_seats,
        'held_seats': held_seats,
        'available_seats': available_seats
    })

@login_required
def book_seat(request, seat_id):
    seat = get_object_or_404(Seat, id=seat_id)
    
    if request.method == 'POST':
        passenger_data = {
            'passenger_name': request.POST.get('passenger_name'),
            'passenger_email': request.POST.get('passenger_email'),
            'passenger_phone': request.POST.get('passenger_phone', '')
        }
        
        try:
            booking = create_booking(seat_id, passenger_data, request.user)
            messages.success(request, f'Seat reserved successfully! Complete payment within 10 minutes.')
            return redirect('booking-detail-gui', booking_id=booking.id)
        except SeatNotAvailableError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'Something went wrong. Please try again.')
            logger.error(f"Booking error: {str(e)}")
    
    return render(request, 'bookings/book_seat.html', {'seat': seat})

@login_required
def booking_list(request):
    if request.user.is_staff:
        # Admin sees all bookings with optimized query
        bookings = Booking.objects.select_related(
            'seat__flight', 'created_by'
        ).order_by('-created_at')[:100]  # Limit to recent 100
    else:
        # Regular users see only their bookings
        bookings = Booking.objects.select_related(
            'seat__flight'
        ).filter(created_by=request.user).order_by('-created_at')
    return render(request, 'bookings/booking_list.html', {'bookings': bookings})

@login_required
def booking_detail(request, booking_id):
    if request.user.is_staff:
        # Admin can view any booking with optimized query
        booking = get_object_or_404(
            Booking.objects.select_related('seat__flight', 'created_by'),
            id=booking_id
        )
    else:
        # Regular users can only view their own bookings
        booking = get_object_or_404(
            Booking.objects.select_related('seat__flight'),
            id=booking_id, created_by=request.user
        )
    return render(request, 'bookings/booking_detail.html', {'booking': booking})

@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    
    if request.method == 'POST':
        return process_booking_payment(request, booking_id)
    
    return render(request, 'bookings/payment.html', {'booking': booking})

@login_required
def process_booking_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    logger.info(f"Processing payment for booking {booking_id} by user {request.user.username}")
    
    try:
        payment_success = process_payment(booking, request.user)
        logger.info(f"Payment result for booking {booking_id}: {payment_success}")
        
        if payment_success:
            messages.success(request, f'Payment processed successfully! Booking confirmed. Reference: {booking.booking_reference}')
        else:
            messages.error(request, 'Payment failed. Please try again or contact support.')
    except (PaymentError, InvalidStateTransitionError) as e:
        logger.error(f"Payment error for booking {booking_id}: {str(e)}")
        messages.error(request, f'Payment failed: {str(e)}') 
    except Exception as e:
        logger.error(f"Unexpected payment error for booking {booking_id}: {str(e)}")
        messages.error(request, f'Payment failed: {str(e)}')
    
    return redirect('booking-detail-gui', booking_id=booking.id)

@login_required
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    
    try:
        cancel_booking(booking, request.user)
        messages.success(request, 'Booking cancelled successfully!')
    except (BookingError, InvalidStateTransitionError) as e:
        messages.error(request, f'Cancellation failed: {str(e)}')
    except Exception as e:
        messages.error(request, f'Cancellation failed: {str(e)}')
    
    return redirect('booking-detail-gui', booking_id=booking.id)

@login_required
def process_refund_view(request, booking_id):
    if not request.user.is_staff:
        messages.error(request, 'Only admin users can process refunds.')
        return redirect('booking-detail-gui', booking_id=booking_id)
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    try:
        refund_booking(booking, request.user)
        messages.success(request, f'Refund processed successfully for booking {booking.booking_reference}')
    except (BookingError, InvalidStateTransitionError) as e:
        messages.error(request, f'Refund failed: {str(e)}')
    except Exception as e:
        messages.error(request, f'Refund failed: {str(e)}')
    
    return redirect('booking-detail-gui', booking_id=booking.id)

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if not first_name or not last_name:
            messages.error(request, 'First name and last name are required.')
            return render(request, 'registration/register.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'registration/register.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            login(request, user)
            messages.success(request, f'Welcome {first_name}! Your account has been created.')
            return redirect('flight-list-gui')
        except Exception as e:
            messages.error(request, 'Registration failed. Please try again.')
            logger.error(f"Registration error: {str(e)}")
    
    return render(request, 'registration/register.html')