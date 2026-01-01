from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Flight, Seat, Booking
from .services import create_booking, process_payment, cancel_booking, refund_booking
from .exceptions import SeatNotAvailableError, BookingError, InvalidStateTransitionError
import logging

logger = logging.getLogger('bookings')

def flight_list(request):
    flights = Flight.objects.filter(is_active=True).order_by('departure_time')
    return render(request, 'bookings/flight_list.html', {'flights': flights})

def flight_seats(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    seats = flight.seats.all().order_by('row_number', 'seat_letter')
    return render(request, 'bookings/flight_seats.html', {
        'flight': flight,
        'seats': seats
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
            messages.success(request, f'Booking created successfully! Reference: {booking.booking_reference}')
            return redirect('booking-detail', booking_id=booking.id)
        except SeatNotAvailableError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'Something went wrong. Please try again.')
            logger.error(f"Booking error: {str(e)}")
    
    return render(request, 'bookings/book_seat.html', {'seat': seat})

@login_required
def booking_list(request):
    bookings = Booking.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'bookings/booking_list.html', {'bookings': bookings})

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    return render(request, 'bookings/booking_detail.html', {'booking': booking})

@login_required
def process_booking_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    
    try:
        process_payment(booking, request.user)
        messages.success(request, 'Payment processed successfully!')
    except Exception as e:
        messages.error(request, f'Payment failed: {str(e)}')
    
    return redirect('booking-detail', booking_id=booking.id)

@login_required
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    
    try:
        cancel_booking(booking, request.user)
        messages.success(request, 'Booking cancelled successfully!')
    except Exception as e:
        messages.error(request, f'Cancellation failed: {str(e)}')
    
    return redirect('booking-detail', booking_id=booking.id)