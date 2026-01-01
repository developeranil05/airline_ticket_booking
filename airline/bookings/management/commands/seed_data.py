from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bookings.models import Flight, Seat
from decimal import Decimal

class Command(BaseCommand):
    help = "Seed database with sample flights and seats"

    def handle(self, *args, **kwargs):
        # Create flights without validation
        flight1 = Flight(
            code='AA101',
            departure_time=timezone.now() + timedelta(days=7),
            arrival_time=timezone.now() + timedelta(days=7, hours=3),
            origin='New York',
            destination='Los Angeles',
            price=Decimal('299.99'),
            aircraft_type='Boeing 737',
            total_seats=150
        )
        flight1.save()
        
        flight2 = Flight(
            code='UA202',
            departure_time=timezone.now() + timedelta(days=8),
            arrival_time=timezone.now() + timedelta(days=8, hours=2),
            origin='Chicago',
            destination='Miami',
            price=Decimal('199.99'),
            aircraft_type='Airbus A320',
            total_seats=180
        )
        flight2.save()
        
        # Create seats
        seats_created = 0
        for flight in [flight1, flight2]:
            for row in range(1, 6):  # 5 rows
                for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                    seat = Seat(
                        flight=flight,
                        seat_number=f"{row}{letter}",
                        seat_class='ECONOMY',
                        row_number=row,
                        seat_letter=letter,
                        is_window=letter in ['A', 'F'],
                        is_aisle=letter in ['C', 'D']
                    )
                    seat.save()
                    seats_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"Created 2 flights and {seats_created} seats successfully!")
        )
