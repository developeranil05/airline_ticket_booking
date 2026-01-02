from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bookings.models import Flight, Seat
from datetime import datetime, timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Populate database with Indian airline flights'

    def handle(self, *args, **options):
        # Indian cities
        cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata',
            'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Kochi'
        ]
        
        # Indian airlines
        airlines = [
            {'code': 'AI', 'name': 'Air India'},
            {'code': 'SG', 'name': 'SpiceJet'},
            {'code': '6E', 'name': 'IndiGo'},
            {'code': 'UK', 'name': 'Vistara'},
            {'code': 'G8', 'name': 'GoAir'},
            {'code': 'I5', 'name': 'AirAsia India'},
            {'code': '9W', 'name': 'Jet Airways'},
            {'code': 'DN', 'name': 'Alliance Air'},
            {'code': 'S2', 'name': 'JetLite'},
            {'code': 'IT', 'name': 'Kingfisher'}
        ]
        
        aircraft_types = ['Boeing 737', 'Airbus A320', 'Boeing 777', 'Airbus A330']
        
        flights_created = 0
        
        for airline in airlines:
            # Create 3-4 flights per airline
            for i in range(random.randint(3, 4)):
                origin = random.choice(cities)
                destination = random.choice([c for c in cities if c != origin])
                
                # Generate flight number
                flight_code = f"{airline['code']}{random.randint(100, 999)}"
                
                # Skip if flight already exists
                if Flight.objects.filter(code=flight_code).exists():
                    continue
                
                # Random departure time (next 30 days)
                departure_time = timezone.now() + timedelta(
                    days=random.randint(1, 30),
                    hours=random.randint(6, 22),
                    minutes=random.choice([0, 15, 30, 45])
                )
                
                # Arrival time (1-5 hours after departure)
                arrival_time = departure_time + timedelta(
                    hours=random.randint(1, 5),
                    minutes=random.choice([0, 15, 30, 45])
                )
                
                # Create flight
                flight = Flight.objects.create(
                    code=flight_code,
                    airline_code=airline['code'],
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    origin=origin,
                    destination=destination,
                    price=random.randint(3000, 15000),
                    aircraft_type=random.choice(aircraft_types),
                    total_seats=random.choice([150, 180, 200]),
                    is_active=True
                )
                
                # Create seats for the flight
                seat_classes = [
                    ('ECONOMY', 140),
                    ('BUSINESS', 20),
                    ('FIRST', 10)
                ]
                
                seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
                row_num = 1
                
                for seat_class, count in seat_classes:
                    seats_created = 0
                    while seats_created < count:
                        for letter in seat_letters:
                            if seats_created >= count:
                                break
                            
                            Seat.objects.create(
                                flight=flight,
                                seat_number=f"{row_num}{letter}",
                                seat_class=seat_class,
                                row_number=row_num,
                                seat_letter=letter,
                                is_window=(letter in ['A', 'F']),
                                is_aisle=(letter in ['C', 'D'])
                            )
                            seats_created += 1
                        row_num += 1
                
                flights_created += 1
                self.stdout.write(f"Created flight {flight_code}: {origin} -> {destination}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {flights_created} flights with seats')
        )