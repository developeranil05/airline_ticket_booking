from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bookings.models import Flight, Seat
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Seed database with sample flights and seats"

    def handle(self, *args, **kwargs):
        flights_created = 0
        seats_created = 0
        
        # Sample flight data
        flight_data = [
            {
                'code': 'AA101',
                'origin': 'New York',
                'destination': 'Los Angeles',
                'price': 299.99,
                'aircraft_type': 'Boeing 737',
                'total_seats': 150
            },
            {
                'code': 'UA202',
                'origin': 'Chicago',
                'destination': 'Miami',
                'price': 199.99,
                'aircraft_type': 'Airbus A320',
                'total_seats': 180
            }
        ]
        
        for data in flight_data:
            flight, created = Flight.objects.get_or_create(
                code=data['code'],
                defaults={
                    'departure_time': timezone.now() + timedelta(days=7),
                    'arrival_time': timezone.now() + timedelta(days=7, hours=3),
                    'origin': data['origin'],
                    'destination': data['destination'],
                    'price': data['price'],
                    'aircraft_type': data['aircraft_type'],
                    'total_seats': data['total_seats']
                }
            )
            
            if created:
                flights_created += 1
                logger.info(f"Created flight: {flight.code}")
                
                # Create sample seats
                for row in range(1, 11):
                    for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                        seat_number = f"{row}{letter}"
                        seat, seat_created = Seat.objects.get_or_create(
                            flight=flight,
                            seat_number=seat_number,
                            defaults={
                                'seat_class': 'ECONOMY',
                                'row_number': row,
                                'seat_letter': letter,
                                'is_window': letter in ['A', 'F'],
                                'is_aisle': letter in ['C', 'D']
                            }
                        )
                        if seat_created:
                            seats_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Database seeded! Created {flights_created} flights and {seats_created} seats."
            )
        )
