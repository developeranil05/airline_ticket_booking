from rest_framework import serializers
from .models import Booking, Flight, Seat
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
import re


class FlightSerializer(serializers.ModelSerializer):
    available_seats = serializers.SerializerMethodField()
    
    class Meta:
        model = Flight
        fields = [
            "id", "code", "departure_time", "arrival_time", 
            "origin", "destination", "price", "aircraft_type", 
            "total_seats", "available_seats", "is_active"
        ]
        
    def get_available_seats(self, obj):
        return obj.seats.filter(is_booked=False).count()
        
    def validate_code(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Flight code must be at least 3 characters long")
        if not re.match(r'^[A-Z0-9]+$', value.upper()):
            raise serializers.ValidationError("Flight code must contain only letters and numbers")
        return value.upper()
    
    def validate_departure_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Departure time must be in the future")
        return value
    
    def validate_arrival_time(self, value):
        departure_time = self.initial_data.get('departure_time')
        if departure_time and value <= datetime.fromisoformat(departure_time.replace('Z', '+00:00')):
            raise serializers.ValidationError("Arrival time must be after departure time")
        return value
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        if value > 50000:
            raise serializers.ValidationError("Price cannot exceed $50,000")
        return value


class SeatSerializer(serializers.ModelSerializer):
    flight_code = serializers.CharField(source='flight.code', read_only=True)
    
    class Meta:
        model = Seat
        fields = [
            "id", "seat_number", "is_booked", "flight", "flight_code", 
            "seat_class", "row_number", "seat_letter", "is_window", "is_aisle"
        ]
        read_only_fields = ["is_booked"]
    
    def validate_seat_number(self, value):
        if not re.match(r'^\d{1,2}[A-F]$', value.upper()):
            raise serializers.ValidationError("Seat number must be in format like '12A' or '5B'")
        return value.upper()
    
    def validate_seat_letter(self, value):
        if value.upper() not in ['A', 'B', 'C', 'D', 'E', 'F']:
            raise serializers.ValidationError("Seat letter must be A-F")
        return value.upper()


class BookingSerializer(serializers.ModelSerializer):
    seat_details = SeatSerializer(source='seat', read_only=True)
    flight_details = FlightSerializer(source='seat.flight', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            "id", "booking_reference", "passenger_name", "passenger_email", 
            "passenger_phone", "seat", "seat_details", "flight_details", 
            "booking_date", "travel_date", "cancelled_date", "confirmed_date", "refund_date",
            "state", "seat_hold_until", "payment_amount", "refund_amount",
            "created_by_name", "updated_by_name", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "booking_reference", "booking_date", "cancelled_date", 
            "confirmed_date", "refund_date", "created_at", "updated_at"
        ]
        
    def validate_passenger_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Passenger name must be at least 2 characters")
        if not re.match(r'^[a-zA-Z\s.]+$', value):
            raise serializers.ValidationError("Passenger name can only contain letters, spaces, and dots")
        return value.strip().title()
        
    def validate_passenger_email(self, value):
        email = value.lower().strip()
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            raise serializers.ValidationError("Invalid email format")
        return email
    
    def validate_passenger_phone(self, value):
        if value and not re.match(r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value
