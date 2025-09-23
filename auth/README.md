# Authentication Module

This module provides JWT-based authentication for the Multi-hop Research Agent using PostgreSQL as the backend database.

## Features

- JWT-based authentication with access and refresh tokens
- User registration and login
- Password hashing with bcrypt
- Session management
- User profile management
- Admin user management
- Password change functionality
- Session tracking and logout

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username (3-50 characters, alphanumeric)
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password
- `is_active`: Account status
- `is_admin`: Admin privileges
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp
- `last_login`: Last login timestamp
- `profile_data`: JSON string for additional user data

### User Sessions Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `session_token`: Refresh token
- `created_at`: Session creation timestamp
- `expires_at`: Session expiration timestamp
- `is_active`: Session status
- `ip_address`: Client IP address
- `user_agent`: Client user agent

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `POST /auth/logout-all` - Logout all user sessions

### User Management
- `GET /auth/me` - Get current user info
- `PUT /auth/me` - Update current user
- `POST /auth/change-password` - Change password
- `GET /auth/sessions` - Get user sessions

### Admin (Admin only)
- `GET /auth/users` - List all users
- `PUT /auth/users/{user_id}/deactivate` - Deactivate user
- `PUT /auth/users/{user_id}/activate` - Activate user
- `PUT /auth/users/{user_id}/admin` - Toggle admin status

## Configuration

Set the following environment variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/research_agent_auth

# JWT
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Usage

### 1. Setup
```bash
python setup_auth.py
```

### 2. Initialize Database
```bash
python -m auth.init_db
```

### 3. Use in Your Application
```python
from auth import auth_router, get_current_active_user, TokenData
from fastapi import FastAPI, Depends

app = FastAPI()
app.include_router(auth_router)

@app.get("/protected")
async def protected_route(current_user: TokenData = Depends(get_current_active_user)):
    return {"user": current_user.username}
```

## Security Features

- Password hashing with bcrypt
- JWT tokens with expiration
- Session management
- IP and user agent tracking
- Admin privilege system
- Account deactivation
- Secure password requirements

## Testing

Run tests with:
```bash
pytest tests/test_auth.py
```

## Dependencies

- `python-jose[cryptography]` - JWT handling
- `passlib[bcrypt]` - Password hashing
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL adapter
- `python-dotenv` - Environment variables
