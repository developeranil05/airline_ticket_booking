from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.generics import ListCreateAPIView
from .models import Seat
from .serializers import SeatSerializer
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView
)
from rest_framework.response import Response
from rest_framework import status
from .models import Booking, Flight
from .serializers import BookingSerializer, FlightSerializer
from .services import (
    create_booking,
    process_payment,
    cancel_booking,
    refund_booking,
)
from .exceptions import SeatNotAvailableError, PaymentError, BookingError, InvalidStateTransitionError
import logging

logger = logging.getLogger('bookings')


# -----------------------
# FLIGHT CRUD APIs
# -----------------------

class FlightListCreateView(ListCreateAPIView):
    queryset = Flight.objects.filter(is_active=True).order_by('departure_time')
    serializer_class = FlightSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        logger.info(f"Flight creation by admin {self.request.user.username}")
        serializer.save(created_by=self.request.user)


class FlightDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer


# -----------------------
# BOOKING APIs
# -----------------------

class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"Booking creation attempt by user {request.user.username}")
        
        # Validate required fields
        seat_id = request.data.get("seat_id")
        passenger_name = request.data.get("passenger_name")
        passenger_email = request.data.get("passenger_email")
        passenger_phone = request.data.get("passenger_phone", "")

        if not all([seat_id, passenger_name, passenger_email]):
            logger.warning(f"Missing required fields in booking request by {request.user.username}")
            return Response({
                "success": False,
                "error": "Missing required fields",
                "message": "seat_id, passenger_name, and passenger_email are required",
                "required_fields": ["seat_id", "passenger_name", "passenger_email"]
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate seat_id is integer
        try:
            seat_id = int(seat_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid seat_id format: {seat_id} by {request.user.username}")
            return Response({
                "success": False,
                "error": "Invalid seat_id",
                "message": "seat_id must be a valid number"
            }, status=status.HTTP_400_BAD_REQUEST)

        passenger_data = {
            'passenger_name': passenger_name.strip(),
            'passenger_email': passenger_email.strip().lower(),
            'passenger_phone': passenger_phone.strip()
        }

        try:
            booking = create_booking(seat_id, passenger_data, request.user)
            logger.info(f"Booking {booking.booking_reference} created successfully by {request.user.username}")
            
            return Response({
                "success": True,
                "message": "Booking created successfully",
                "data": BookingSerializer(booking).data,
                "booking_reference": str(booking.booking_reference)
            }, status=status.HTTP_201_CREATED)
            
        except SeatNotAvailableError as e:
            logger.warning(f"Seat unavailable for booking by {request.user.username}: {str(e)}")
            return Response({
                "success": False,
                "error": "Seat not available",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Unexpected error in booking creation by {request.user.username}: {str(e)}")
            return Response({
                "success": False,
                "error": "Internal server error",
                "message": "Something went wrong. Please try again later."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        logger.info(f"Payment attempt for booking {pk} by user {request.user.username}")
        
        try:
            booking = Booking.objects.get(pk=pk)
            
            # Check if user owns the booking or is admin
            if booking.created_by != request.user and not request.user.is_staff:
                logger.warning(f"Unauthorized payment attempt for booking {pk} by {request.user.username}")
                return Response({
                    "success": False,
                    "error": "Unauthorized",
                    "message": "You can only process payment for your own bookings"
                }, status=status.HTTP_403_FORBIDDEN)
            
            process_payment(booking, request.user)
            logger.info(f"Payment processed for booking {booking.booking_reference} by {request.user.username}")
            
            return Response({
                "success": True,
                "message": "Payment processed successfully",
                "booking_reference": str(booking.booking_reference),
                "status": booking.state,
                "payment_amount": str(booking.payment_amount)
            })
            
        except Booking.DoesNotExist:
            logger.warning(f"Payment attempt for non-existent booking {pk} by {request.user.username}")
            return Response({
                "success": False,
                "error": "Booking not found",
                "message": f"No booking found with ID {pk}"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except (PaymentError, InvalidStateTransitionError) as e:
            logger.warning(f"Payment failed for booking {pk}: {str(e)}")
            return Response({
                "success": False,
                "error": "Payment failed",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CancelView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        logger.info(f"Cancellation attempt for booking {pk} by user {request.user.username}")
        
        try:
            booking = Booking.objects.get(pk=pk)
            
            # Check if user owns the booking or is admin
            if booking.created_by != request.user and not request.user.is_staff:
                logger.warning(f"Unauthorized cancellation attempt for booking {pk} by {request.user.username}")
                return Response({
                    "success": False,
                    "error": "Unauthorized",
                    "message": "You can only cancel your own bookings"
                }, status=status.HTTP_403_FORBIDDEN)
            
            cancel_booking(booking, request.user)
            logger.info(f"Booking {booking.booking_reference} cancelled by {request.user.username}")
            
            return Response({
                "success": True,
                "message": "Booking cancelled successfully",
                "booking_reference": str(booking.booking_reference),
                "status": booking.state,
                "cancelled_date": booking.cancelled_date
            })
            
        except Booking.DoesNotExist:
            logger.warning(f"Cancellation attempt for non-existent booking {pk} by {request.user.username}")
            return Response({
                "success": False,
                "error": "Booking not found",
                "message": f"No booking found with ID {pk}"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except (BookingError, InvalidStateTransitionError) as e:
            logger.warning(f"Cancellation failed for booking {pk}: {str(e)}")
            return Response({
                "success": False,
                "error": "Cancellation failed",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RefundView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        logger.info(f"Refund attempt for booking {pk} by user {request.user.username}")
        
        try:
            booking = Booking.objects.get(pk=pk)
            
            # Check if user owns the booking or is admin
            if booking.created_by != request.user and not request.user.is_staff:
                logger.warning(f"Unauthorized refund attempt for booking {pk} by {request.user.username}")
                return Response({
                    "success": False,
                    "error": "Unauthorized",
                    "message": "You can only request refund for your own bookings"
                }, status=status.HTTP_403_FORBIDDEN)
            
            refund_booking(booking, request.user)
            logger.info(f"Refund processed for booking {booking.booking_reference} by {request.user.username}")
            
            return Response({
                "success": True,
                "message": "Refund processed successfully",
                "booking_reference": str(booking.booking_reference),
                "status": booking.state,
                "refund_amount": str(booking.refund_amount),
                "refund_date": booking.refund_date
            })
            
        except Booking.DoesNotExist:
            logger.warning(f"Refund attempt for non-existent booking {pk} by {request.user.username}")
            return Response({
                "success": False,
                "error": "Booking not found",
                "message": f"No booking found with ID {pk}"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except (BookingError, InvalidStateTransitionError) as e:
            logger.warning(f"Refund failed for booking {pk}: {str(e)}")
            return Response({
                "success": False,
                "error": "Refund failed",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SeatListCreateView(ListCreateAPIView):
    serializer_class = SeatSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = Seat.objects.all()
        flight_id = self.request.query_params.get('flight_id')
        available_only = self.request.query_params.get('available_only')
        
        if flight_id:
            queryset = queryset.filter(flight_id=flight_id)
        if available_only == 'true':
            queryset = queryset.filter(is_booked=False)
            
        return queryset.select_related('flight')
    
    def perform_create(self, serializer):
        logger.info(f"Seat creation by admin {self.request.user.username}")
        serializer.save(created_by=self.request.user)


class BookingListView(ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all().select_related('seat__flight', 'created_by')
        return Booking.objects.filter(created_by=self.request.user).select_related('seat__flight')