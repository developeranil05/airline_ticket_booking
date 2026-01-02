from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password, check_password
import uuid

class BookingState(models.TextChoices):
    INITIATED = "INITIATED"
    SEAT_HELD = "SEAT_HELD"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REFUNDED = "REFUNDED"


class Flight(models.Model):
    code = models.CharField(max_length=10, unique=True, db_index=True)
    airline_code = models.CharField(max_length=2, default='AI', db_index=True)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    origin = models.CharField(max_length=100, db_index=True)
    destination = models.CharField(max_length=100, db_index=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    aircraft_type = models.CharField(max_length=50, default='Boeing 737')
    total_seats = models.PositiveIntegerField(default=180)
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_flights'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_flights'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'airline_flights'
        ordering = ['departure_time']
        indexes = [
            models.Index(fields=['departure_time', 'origin', 'destination']),
            models.Index(fields=['is_active', 'departure_time']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if hasattr(self, 'arrival_time') and hasattr(self, 'departure_time'):
            if self.arrival_time and self.departure_time and self.arrival_time <= self.departure_time:
                raise ValidationError('Arrival time must be after departure time')
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only validate on creation, not updates
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.origin} to {self.destination}"


class Seat(models.Model):
    SEAT_CLASS_CHOICES = [
        ('ECONOMY', 'Economy'),
        ('BUSINESS', 'Business'),
        ('FIRST', 'First Class')
    ]
    
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=5)
    is_booked = models.BooleanField(default=False, db_index=True)
    seat_class = models.CharField(
        max_length=20, 
        choices=SEAT_CLASS_CHOICES, 
        default='ECONOMY'
    )
    row_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    seat_letter = models.CharField(max_length=1)
    is_window = models.BooleanField(default=False)
    is_aisle = models.BooleanField(default=False)
    
    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_seats'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_seats'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'airline_seats'
        unique_together = [("flight", "seat_number")]
        indexes = [
            models.Index(fields=['flight', 'is_booked']),
            models.Index(fields=['seat_class', 'is_booked']),
        ]

    def __str__(self):
        return f"{self.flight.code}-{self.seat_number}"


class Booking(models.Model):
    booking_reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='bookings')
    passenger_name = models.CharField(max_length=100)
    passenger_email = models.EmailField()
    passenger_phone = models.CharField(max_length=20, blank=True)
    
    # Booking dates
    booking_date = models.DateTimeField(auto_now_add=True)
    travel_date = models.DateField(null=True, blank=True)
    cancelled_date = models.DateTimeField(null=True, blank=True)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    
    state = models.CharField(
        max_length=20,
        choices=BookingState.choices,
        default=BookingState.INITIATED,
        db_index=True
    )
    seat_hold_until = models.DateTimeField(null=True, blank=True)
    payment_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    payment_reference = models.CharField(max_length=100, blank=True)
    refund_processed = models.BooleanField(default=False)
    refund_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    refund_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_bookings'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_bookings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'airline_bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state', 'created_at']),
            models.Index(fields=['seat_hold_until']),
            models.Index(fields=['passenger_email']),
            models.Index(fields=['booking_date']),
            models.Index(fields=['travel_date']),
            models.Index(fields=['cancelled_date']),
        ]

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.state}"


class MonitoringUser(models.Model):
    username = models.CharField(max_length=150, unique=True, db_index=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True, db_index=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'monitoring_users'
        ordering = ['username']
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def update_last_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
    
    def __str__(self):
        return self.username


class AdminUser(models.Model):
    AIRLINE_CHOICES = [
        ('AI', 'Air India'),
        ('SG', 'SpiceJet'),
        ('6E', 'IndiGo'),
        ('UK', 'Vistara'),
        ('G8', 'GoAir'),
        ('I5', 'AirAsia India'),
        ('9W', 'Jet Airways'),
        ('DN', 'Alliance Air'),
        ('S2', 'JetLite'),
        ('IT', 'Kingfisher'),
    ]
    
    admin_name = models.CharField(max_length=100, default='Admin')
    airline_code = models.CharField(max_length=2, choices=AIRLINE_CHOICES, db_index=True)
    airline_name = models.CharField(max_length=100, default='Unknown')
    email = models.EmailField(default='admin@airline.com')
    phone_number = models.CharField(max_length=15, default='+91-9876543210')
    password = models.CharField(max_length=128)
    actual_password = models.CharField(max_length=50, default='admin123')  # Store actual password for monitoring
    is_active = models.BooleanField(default=True, db_index=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_users'
        ordering = ['airline_code', 'admin_name']
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def update_last_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
    
    def __str__(self):
        return f"{self.airline_code} - {self.admin_name}"
