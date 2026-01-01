from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Seat, Booking
from .services import create_booking, process_payment, cancel_booking, refund_booking
from .serializers import BookingSerializer
from .exceptions import SeatNotAvailableError, BookingError, PaymentError
import logging

logger = logging.getLogger('bookings')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking_api(request):
    try:
        seat_id = request.data.get('seat_id')
        passenger_data = {
            'passenger_name': request.data.get('passenger_name'),
            'passenger_email': request.data.get('passenger_email'),
            'passenger_phone': request.data.get('passenger_phone', '')
        }
        
        booking = create_booking(seat_id, passenger_data, request.user)
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except SeatNotAvailableError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Booking creation error: {str(e)}")
        return Response({'error': 'Booking failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment_api(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, created_by=request.user)
        success = process_payment(booking, request.user)
        
        if success:
            serializer = BookingSerializer(booking)
            return Response(serializer.data)
        else:
            return Response({'error': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)
            
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking_api(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, created_by=request.user)
        cancel_booking(booking, request.user)
        serializer = BookingSerializer(booking)
        return Response(serializer.data)
        
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except BookingError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refund_booking_api(request, booking_id):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
    try:
        booking = Booking.objects.get(id=booking_id)
        refund_booking(booking, request.user)
        serializer = BookingSerializer(booking)
        return Response(serializer.data)
        
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except BookingError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)