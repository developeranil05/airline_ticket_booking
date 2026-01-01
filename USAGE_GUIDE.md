# Airline Booking System - Usage Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install Django djangorestframework psycopg2-binary
```

### 2. Setup Database
```bash
cd airline
python manage.py makemigrations bookings
python manage.py migrate
```

### 3. Create Admin User
```bash
python manage.py createsuperuser
# Enter username, email, and password when prompted
```

### 4. Load Sample Data
```bash
python manage.py seed_data
```

### 5. Start Server
```bash
python manage.py runserver
```

## 🌐 Access URLs

### Web Interface (GUI)
- **Home Page:** http://127.0.0.1:8000/
- **Flight List:** http://127.0.0.1:8000/
- **My Bookings:** http://127.0.0.1:8000/my-bookings/
- **Admin Panel:** http://127.0.0.1:8000/admin/

### API Endpoints
- **Flights API:** http://127.0.0.1:8000/api/flights/
- **Seats API:** http://127.0.0.1:8000/api/seats/
- **Bookings API:** http://127.0.0.1:8000/api/bookings/

## 👤 How to Use

### For End Users (Web Interface):

1. **Browse Flights**
   - Visit http://127.0.0.1:8000/
   - View available flights with prices and schedules

2. **Select Seats**
   - Click "View Seats" on any flight
   - See visual seat map with availability
   - Green = Available, Red = Booked

3. **Make Booking**
   - Click on available seat
   - Fill passenger details
   - Click "Book Seat"

4. **Complete Payment**
   - Go to "My Bookings"
   - Click "Pay Now" for pending bookings
   - Payment will be processed automatically

5. **Manage Bookings**
   - View all bookings in "My Bookings"
   - Cancel confirmed bookings if needed

### For Developers (API):

#### Authentication Required
```bash
# Login first to get session
curl -X POST http://127.0.0.1:8000/admin/login/ \
  -d "username=admin&password=yourpassword"
```

#### Create Booking
```bash
curl -X POST http://127.0.0.1:8000/api/book/ \
  -H "Content-Type: application/json" \
  -d '{
    "seat_id": 1,
    "passenger_name": "John Doe",
    "passenger_email": "john@example.com",
    "passenger_phone": "+1234567890"
  }'
```

#### Process Payment
```bash
curl -X POST http://127.0.0.1:8000/api/bookings/1/pay/
```

## 🔧 Admin Tasks

### Add Flights (Admin Panel)
1. Go to http://127.0.0.1:8000/admin/
2. Login with superuser credentials
3. Click "Flights" → "Add Flight"
4. Fill flight details and save

### Add Seats (Admin Panel)
1. In admin panel, click "Seats" → "Add Seat"
2. Select flight and enter seat details
3. Or use the seed_data command for bulk creation

### Monitor Bookings
1. In admin panel, click "Bookings"
2. View all bookings with filters
3. Check booking states and passenger details

## 📱 Features

### Web Interface Features:
- ✅ Responsive design (mobile-friendly)
- ✅ Visual seat selection
- ✅ Real-time availability
- ✅ Booking management
- ✅ Payment processing
- ✅ User authentication

### API Features:
- ✅ RESTful endpoints
- ✅ JSON responses
- ✅ Authentication required
- ✅ Error handling
- ✅ Comprehensive logging

## 🛠️ Troubleshooting

### Common Issues:

1. **Django not installed**
   ```bash
   pip install Django
   ```

2. **Database errors**
   ```bash
   python manage.py migrate
   ```

3. **No flights showing**
   ```bash
   python manage.py seed_data
   ```

4. **Permission denied**
   - Make sure you're logged in
   - Create superuser if needed

## 📊 Database Tables

- **airline_flights** - Flight information
- **airline_seats** - Seat details
- **airline_bookings** - Booking records
- **auth_user** - User accounts

## 🔍 Logs

Check logs at: `airline/logs/airline.log`

## 🎯 Next Steps

1. Customize flight schedules
2. Add more seat classes
3. Integrate real payment gateway
4. Add email notifications
5. Deploy to production server