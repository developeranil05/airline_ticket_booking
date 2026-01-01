from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Booking
from bookings.state_machine import transition
from bookings.exceptions import InvalidStateTransitionError
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Expire seat holds after 10 minutes"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        bookings = Booking.objects.filter(
            state="SEAT_HELD",
            seat_hold_until__lt=now
        )

        expired_count = 0
        failed_count = 0

        for booking in bookings:
            try:
                transition(booking, "EXPIRED")
                expired_count += 1
            except InvalidStateTransitionError as e:
                logger.error(f"Failed to expire booking {booking.id}: {e}")
                failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Expired {expired_count} booking(s)")
        )
        
        if failed_count > 0:
            self.stdout.write(
                self.style.WARNING(f"Failed to expire {failed_count} booking(s)")
            )
