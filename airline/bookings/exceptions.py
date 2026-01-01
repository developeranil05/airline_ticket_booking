class BookingError(Exception):
    """Base exception for booking-related errors"""
    pass

class InvalidStateTransitionError(BookingError):
    """Raised when an invalid state transition is attempted"""
    pass

class SeatNotAvailableError(BookingError):
    """Raised when trying to book an unavailable seat"""
    pass

class PaymentError(BookingError):
    """Raised when payment processing fails"""
    pass

class BookingExpiredError(BookingError):
    """Raised when trying to operate on an expired booking"""
    pass