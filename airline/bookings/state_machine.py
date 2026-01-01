from .exceptions import InvalidStateTransitionError

ALLOWED_TRANSITIONS = {
    "INITIATED": ["SEAT_HELD"],
    "SEAT_HELD": ["PAYMENT_PENDING", "EXPIRED", "CANCELLED"],
    "PAYMENT_PENDING": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["CANCELLED"],
    "CANCELLED": ["REFUNDED"],
}

def transition(booking, next_state):
    if next_state not in ALLOWED_TRANSITIONS.get(booking.state, []):
        raise InvalidStateTransitionError(f"Invalid transition {booking.state} → {next_state}")
    booking.state = next_state
    booking.save()
