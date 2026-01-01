from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Booking
from bookings.state_machine import transition

class Command(BaseCommand):
    help = 'Expire seat holds that have exceeded 10 minutes'

    def handle(self, *args, **options):
        expired_bookings = Booking.objects.filter(
            state='SEAT_HELD',
            seat_hold_until__lt=timezone.now()
        )
        
        count = 0
        for booking in expired_bookings:
            try:
                transition(booking, 'EXPIRED')
                count += 1
            except Exception as e:
                self.stdout.write(f'Error expiring booking {booking.id}: {e}')
        
        self.stdout.write(f'Expired {count} seat holds')