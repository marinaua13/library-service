# Library Service :relaxed:

## Description
This project is a library management system built using Django and Django REST Framework. It includes functionality for managing books, users, borrowings, payments, and notifications. The system integrates with Stripe for handling payments and Telegram for sending notifications. 

## Features

### User Registration and Authentication
- Users can register with their email and password to create an account.
- Users can log in with their credentials and receive a token for authentication.

### User Profile
- Users can create and update their profile
### Borrowings Service 
- **Functionality**: Managing users' borrowings of books 
- **API**: 
- **POST** `borrowings/` - Add new borrowing (inventory should be decremented by 1) 
- **GET** `borrowings/?user_id=...&is_active=...` - Get borrowings by user ID and active status 
- **GET** `borrowings/<id>/` - Get specific borrowing 
- **POST** `borrowings/<id>/return/` - Set actual return date (inventory should be incremented by 1) 
### Notifications Service (Telegram) 
- **Functionality**: Notifications about new borrowing creation, borrowings overdue 
- **Setup**: - Django Celery for parallel processing - Uses Telegram API, Telegram Chats & Bots 
### Payments Service (Stripe) 
- **Functionality**: Perform payments for book borrowings 
- **API**: 
- **GET** `stripe/success/` - Check successful Stripe payment 
- **GET** `cancel/` - Return payment to status PENDING
- `**POST**  `/webhooks/stripe/` - Handle Stripe webhooks
### Coding 
- Implement CRUD functionality for Books Service 
   - Initialize books app 
   - Add book model, serializer, and views 
   - Implement permissions (admin only for CRUD, all users for listing) 
   - Use JWT token authentication 
- Implement CRUD for Users Service 
   - Initialize users app 
   - Add user model with email and JWT support 
   - Update JWT header for better experience 
- Implement Borrowing List & Detail endpoint 
   - Initialize borrowings app 
   - Implement serializers and endpoints 
   - Validate book inventory and handle borrowing logic 
   - Add filtering for borrowings 
- Implement Return Borrowing functionality 
   - Ensure single return and inventory update 
   - Set up notifications for new borrowings and overdue checks 
   - Use Telegram API and setup bots 
- Implement Payments functionality 
   - Create Payment model and endpoints 
   - Integrate Stripe for payments 
   - Handle success and cancel URLs 
- Implement FINE payments for overdue books


## Installation

1. **Clone the repository**
    ```sh
    git clone https://github.com/marinaua13/library-service/
    cd library-service
    ```

2. **Create a virtual environment and activate it**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**
    ```sh
    pip install -r requirements.txt
    ```

4. **Apply migrations**
    ```sh
    python manage.py migrate
    ```

5. **Create a superuser**
    ```sh
    python manage.py createsuperuser
    ```

6. **Run the development server**
    ```sh
    python manage.py runserver
    ```

### Additional data:
You can use the following data to get token:
    email: oz@gmail.com
    password: oz12345

Or you can make new registration 
- `POST /api/user/register/` - Register a new user
:relaxed:

### Documentation
The API documentation is available at `api/doc/swagger/`. It includes sample API requests and responses for different endpoints.


