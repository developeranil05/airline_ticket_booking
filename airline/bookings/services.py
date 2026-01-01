import random
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Seat, Booking
from .state_machine import transition
from .exceptions import SeatNotAvailableError, PaymentError, BookingError
import logging

logger = logging.getLogger('bookings')

@transaction.atomic
def create_booking(seat_id, passenger_data, user=None):
    logger.info(f"Creating booking for seat {seat_id} by user {user.username if user else 'Anonymous'}")
    
    seat = Seat.objects.select_for_update().filter(id=seat_id).first()

    if not seat:
        logger.warning(f"Seat {seat_id} does not exist")
        raise SeatNotAvailableError("Seat does not exist")

    if seat.is_booked:
        logger.warning(f"Seat {seat_id} already booked")
        raise SeatNotAvailableError("Seat already booked")
    
    # Check if flight is in the future
    if seat.flight.departure_time <= timezone.now():
        logger.warning(f"Cannot book seat for past flight {seat.flight.code}")
        raise SeatNotAvailableError("Cannot book seats for flights that have already departed")

    booking = Booking.objects.create(
        seat=seat,
        user=user,
        passenger_name=passenger_data.get('passenger_name'),
        passenger_email=passenger_data.get('passenger_email'),
        passenger_phone=passenger_data.get('passenger_phone', ''),
        travel_date=seat.flight.departure_time.date(),
        state="INITIATED",
        seat_hold_until=timezone.now() + timedelta(minutes=10),
        payment_amount=seat.flight.price,
        created_by=user
    )
    
    # Follow state machine: INITIATED → SEAT_HELD
    transition(booking, "SEAT_HELD")
    
    logger.info(f"Booking {booking.booking_reference} created successfully")
    return booking


def mock_payment():
    return random.choice(["SUCCESS", "FAILURE"])


@transaction.atomic
def process_payment(booking, user=None):
    # Follow state machine: SEAT_HELD → PAYMENT_PENDING
    transition(booking, "PAYMENT_PENDING")

    payment_result = mock_payment()
    
    if payment_result == "SUCCESS":
        # PAYMENT_PENDING → CONFIRMED
        transition(booking, "CONFIRMED")
        booking.seat.is_booked = True
        booking.seat.save()
        booking.confirmed_date = timezone.now()
        booking.updated_by = user
        booking.save()
        return True
    else:
        # PAYMENT_PENDING → CANCELLED
        transition(booking, "CANCELLED")
        return False


@transaction.atomic
def cancel_booking(booking, user=None):
    if booking.state != "CONFIRMED":
        raise BookingError("Only confirmed bookings can be cancelled")
    
    # CONFIRMED → CANCELLED
    transition(booking, "CANCELLED")
    
    # Free up the seat
    booking.seat.is_booked = False
    booking.seat.save()
    
    booking.cancelled_date = timezone.now()
    booking.updated_by = user
    booking.save()


@transaction.atomic
def refund_booking(booking, user=None):
    if booking.refund_processed:
        raise BookingError("Refund already processed")
    if booking.state != "CANCELLED":
        raise BookingError("Only cancelled bookings can be refunded")

    # CANCELLED → REFUNDED
    transition(booking, "REFUNDED")
    
    booking.refund_processed = True
    booking.refund_date = timezone.now()
    booking.refund_amount = booking.payment_amount
    booking.updated_by = user
    booking.save()
