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
    logger.info(f"Flight list accessed with params: {request.GET}")
    
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    date = request.GET.get('date', '')
    passengers = request.GET.get('passengers', '1')
    
    flights = Flight.objects.filter(is_active=True)
    logger.info(f"Total active flights: {flights.count()}")
    
    if origin:
        flights = flights.filter(origin__icontains=origin)
        logger.info(f"After origin filter '{origin}': {flights.count()}")
    if destination:
        flights = flights.filter(destination__icontains=destination)
        logger.info(f"After destination filter '{destination}': {flights.count()}")
    if date:
        flights = flights.filter(departure_time__date=date)
        logger.info(f"After date filter '{date}': {flights.count()}")
    
    flights = flights.order_by('departure_time')[:20]
    logger.info(f"Final flights count: {len(flights)}")
    
    # Add seat statistics
    for flight in flights:
        total_seats = flight.seats.count()
        booked_seats = flight.seats.filter(is_booked=True).count()
        available_seats = total_seats - booked_seats
        
        flight.total_seats_count = total_seats
        flight.booked_seats_count = booked_seats
        flight.available_seats_count = available_seats
        logger.info(f"Flight {flight.code}: {available_seats}/{total_seats} available")
    
    return render(request, 'bookings/flight_list_simple.html', {
        'flights': flights,
        'origin': origin,
        'destination': destination,
        'date': date,
        'passengers': passengers
    })

def flight_seats(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    
    # Get passenger count from session or URL parameter
    passengers = int(request.GET.get('passengers', request.session.get('passengers', 1)))
    request.session['passengers'] = passengers
    
    # Get previously selected seats
    selected_seat_numbers = request.GET.get('selected', '').split(',') if request.GET.get('selected') else []
    
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
    
    return render(request, 'bookings/flight_seats_premium.html', {
        'flight': flight,
        'seats': seats,
        'total_seats': total_seats,
        'booked_seats': booked_seats,
        'held_seats': held_seats,
        'available_seats': available_seats,
        'passengers': passengers,
        'selected_seat_numbers': selected_seat_numbers
    })

@login_required
def book_seat(request, seat_id):
    seat = get_object_or_404(Seat, id=seat_id)
    passengers = int(request.GET.get('passengers', request.session.get('passengers', 1)))
    
    # Get selected seats information
    seat_numbers = request.GET.get('seat_numbers', seat.seat_number).split(',')
    selected_seats = seat_numbers[:passengers]  # Ensure we don't exceed passenger count
    
    total_price = seat.flight.price * passengers
    
    if request.method == 'POST':
        try:
            bookings_created = []
            
            if passengers > 1:
                # Handle multiple passengers - create separate bookings for each
                for i in range(1, passengers + 1):
                    passenger_data = {
                        'passenger_name': request.POST.get(f'passenger_name_{i}'),
                        'passenger_email': request.POST.get(f'passenger_email_{i}'),
                        'passenger_phone': request.POST.get(f'passenger_phone_{i}', '')
                    }
                    
                    # Find the corresponding seat for this passenger
                    if i <= len(selected_seats):
                        # Find seat by seat number
                        try:
                            passenger_seat = Seat.objects.get(
                                flight=seat.flight, 
                                seat_number=selected_seats[i-1]
                            )
                            booking = create_booking(passenger_seat.id, passenger_data, request.user)
                            bookings_created.append(booking)
                        except Seat.DoesNotExist:
                            messages.error(request, f'Seat {selected_seats[i-1]} not found.')
                            return redirect('flight-seats-gui', flight_id=seat.flight.id)
            else:
                # Single passenger
                passenger_data = {
                    'passenger_name': request.POST.get('passenger_name'),
                    'passenger_email': request.POST.get('passenger_email'),
                    'passenger_phone': request.POST.get('passenger_phone', '')
                }
                booking = create_booking(seat_id, passenger_data, request.user)
                bookings_created.append(booking)
            
            if bookings_created:
                # Redirect to the first booking's detail page
                messages.success(request, f'{len(bookings_created)} seat(s) reserved successfully! Complete payment within 10 minutes.')
                return redirect('booking-detail-gui', booking_id=bookings_created[0].id)
            
        except SeatNotAvailableError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'Something went wrong. Please try again.')
            logger.error(f"Booking error: {str(e)}")
    
    return render(request, 'bookings/book_seat.html', {
        'seat': seat,
        'passengers': passengers,
        'total_price': total_price,
        'selected_seats': selected_seats
    })

@login_required
def booking_list(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    origin_filter = request.GET.get('origin', '')
    destination_filter = request.GET.get('destination', '')
    
    if request.user.is_staff:
        # Admin sees all bookings with optimized query
        bookings = Booking.objects.select_related(
            'seat__flight', 'created_by'
        ).order_by('-created_at')
    else:
        # Regular users see only their bookings
        bookings = Booking.objects.select_related(
            'seat__flight'
        ).filter(created_by=request.user).order_by('-created_at')
    
    # Apply filters
    if status_filter:
        bookings = bookings.filter(state=status_filter)
    if origin_filter:
        bookings = bookings.filter(seat__flight__origin__icontains=origin_filter)
    if destination_filter:
        bookings = bookings.filter(seat__flight__destination__icontains=destination_filter)
    
    # Limit results for performance
    if request.user.is_staff:
        bookings = bookings[:100]
    
    return render(request, 'bookings/booking_list.html', {
        'bookings': bookings,
        'status_filter': status_filter,
        'origin_filter': origin_filter,
        'destination_filter': destination_filter
    })

@login_required
def booking_detail(request, booking_id):
    try:
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
    except:
        messages.error(request, 'Booking not found or access denied.')
        return redirect('booking-list-gui')
    
    # Get related bookings (same flight, same user, created around the same time)
    from django.utils import timezone
    from datetime import timedelta
    
    related_bookings = Booking.objects.filter(
        seat__flight=booking.seat.flight,
        created_by=booking.created_by,
        created_at__gte=booking.created_at - timedelta(minutes=5),
        created_at__lte=booking.created_at + timedelta(minutes=5)
    ).exclude(id=booking.id).select_related('seat')
    
    # Calculate total payment amount for all related bookings
    total_payment = booking.payment_amount or 0
    for related in related_bookings:
        total_payment += related.payment_amount or 0
    
    return render(request, 'bookings/booking_detail.html', {
        'booking': booking,
        'related_bookings': related_bookings,
        'total_payment': total_payment
    })

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

@login_required
def edit_passenger(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    
    if request.method == 'POST':
        booking.passenger_name = request.POST.get('passenger_name')
        booking.passenger_email = request.POST.get('passenger_email')
        booking.passenger_phone = request.POST.get('passenger_phone', '')
        booking.save()
        messages.success(request, 'Passenger details updated successfully!')
        return redirect('booking-detail-gui', booking_id=booking.id)
    
    return render(request, 'bookings/edit_passenger.html', {'booking': booking})

@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    
    if booking.state not in ['SEAT_HELD', 'INITIATED']:
        messages.error(request, 'Cannot delete confirmed or processed bookings.')
        return redirect('booking-detail-gui', booking_id=booking.id)
    
    if request.method == 'POST':
        # Release the seat
        booking.seat.is_booked = False
        booking.seat.save()
        
        # Delete the booking
        booking.delete()
        messages.success(request, 'Booking deleted successfully!')
        return redirect('booking-list-gui')
    
    return render(request, 'bookings/confirm_delete.html', {'booking': booking})

@login_required
def change_passengers(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, created_by=request.user)
    
    if booking.state not in ['SEAT_HELD', 'INITIATED']:
        messages.error(request, 'Cannot modify confirmed bookings.')
        return redirect('booking-detail-gui', booking_id=booking.id)
    
    # Get related bookings count
    from datetime import timedelta
    related_count = Booking.objects.filter(
        seat__flight=booking.seat.flight,
        created_by=booking.created_by,
        created_at__gte=booking.created_at - timedelta(minutes=5),
        created_at__lte=booking.created_at + timedelta(minutes=5)
    ).count()
    
    current_passengers = related_count
    
    if request.method == 'POST':
        new_passengers = int(request.POST.get('passengers', 1))
        
        # Redirect to seat selection with new passenger count
        request.session['passengers'] = new_passengers
        messages.info(request, f'Passenger count changed to {new_passengers}. Please select seats.')
        return redirect('flight-seats-gui', flight_id=booking.seat.flight.id)
    
    return render(request, 'bookings/change_passengers.html', {
        'booking': booking,
        'current_passengers': current_passengers
    })

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