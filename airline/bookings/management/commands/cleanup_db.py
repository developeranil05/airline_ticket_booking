from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking

class Command(BaseCommand):
    help = 'Clean up old expired bookings to improve performance'

    def handle(self, *args, **options):
        # Delete expired bookings older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        
        old_expired = Booking.objects.filter(
            state='EXPIRED',
            updated_at__lt=cutoff_date
        )
        
        count = old_expired.count()
        old_expired.delete()
        
        self.stdout.write(f'Cleaned up {count} old expired bookings')