#!/usr/bin/env python
import os
import sys
import django
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airline.settings')
django.setup()

from bookings.models import Booking
from bookings.state_machine import transition
from django.utils import timezone

def expire_seat_holds():
    """Expire seat holds that have exceeded 10 minutes"""
    expired_bookings = Booking.objects.filter(
        state='SEAT_HELD',
        seat_hold_until__lt=timezone.now()
    )
    
    count = 0
    for booking in expired_bookings:
        try:
            transition(booking, 'EXPIRED')
            count += 1
            print(f"Expired booking {booking.booking_reference}")
        except Exception as e:
            print(f"Error expiring booking {booking.id}: {e}")
    
    if count > 0:
        print(f"Expired {count} seat holds at {datetime.now()}")

if __name__ == "__main__":
    print("Starting seat hold expiration scheduler...")
    while True:
        expire_seat_holds()
        time.sleep(60)  # Check every minute