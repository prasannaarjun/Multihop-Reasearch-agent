# Authentication Features

This document describes the authentication system integrated into the Multi-hop Research Agent frontend.

## Overview

The frontend now includes a complete authentication system that integrates with the FastAPI backend's JWT-based authentication. Users must be logged in to access the research and chat features.

## Features

### 🔐 User Authentication
- **User Registration**: New users can create accounts with username, email, password, and full name
- **User Login**: Existing users can sign in with email and password
- **Automatic Token Management**: Access and refresh tokens are automatically managed
- **Session Persistence**: Users remain logged in across browser sessions

### 👤 User Profile Management
- **Profile Viewing**: Users can view their account information
- **Profile Editing**: Users can update their username, email, and full name
- **Password Changes**: Secure password change functionality
- **Session Management**: View and manage active sessions

### 🛡️ Security Features
- **JWT Token Authentication**: Secure token-based authentication
- **Automatic Token Refresh**: Tokens are automatically refreshed when needed
- **Protected Routes**: All research and chat features require authentication
- **Session Logout**: Users can logout from current or all sessions

### 🎨 User Interface
- **Consistent Styling**: Authentication components follow the existing design system
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Loading States**: Proper loading indicators during authentication operations
- **Error Handling**: Clear error messages for authentication failures

## Components

### Authentication Components
- **Login**: User login form with validation
- **Register**: User registration form with validation
- **UserProfile**: Profile management modal with tabs for profile, security, and sessions
- **ProtectedRoute**: Component to guard authenticated routes

### Context and Services
- **AuthContext**: React context for managing authentication state
- **AuthProvider**: Provider component that wraps the app
- **apiService**: Updated with authentication methods and automatic token handling

## Usage

### For Users
1. **First Time Users**: Click "Sign up here" on the login page to create an account
2. **Existing Users**: Enter your email and password to sign in
3. **Profile Management**: Click the "👤 Profile" button in the header to manage your account
4. **Logout**: Click the "🚪 Logout" button in the header to sign out

### For Developers
The authentication system is fully integrated and requires no additional setup. The `useAuth` hook provides access to authentication state and methods:

```javascript
import { useAuth } from './contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();
  
  // Use authentication state and methods
}
```

## API Integration

The frontend automatically handles:
- **Token Storage**: Access and refresh tokens are stored in localStorage
- **Request Headers**: Authorization headers are automatically added to API requests
- **Token Refresh**: Expired tokens are automatically refreshed
- **Error Handling**: Authentication errors are handled gracefully

## Security Considerations

- **Token Storage**: Tokens are stored in localStorage (consider httpOnly cookies for production)
- **HTTPS**: Ensure HTTPS is used in production for secure token transmission
- **Token Expiration**: Tokens have limited lifetimes and are automatically refreshed
- **Session Management**: Users can logout from all sessions for security

## Styling

All authentication components follow the existing design system:
- **Color Scheme**: Uses the same blue (#667eea) and gray color palette
- **Typography**: Consistent font sizes and weights
- **Spacing**: Follows the established spacing patterns
- **Responsive**: Mobile-first responsive design
- **Accessibility**: Proper focus states and keyboard navigation

## Error Handling

The system handles various error scenarios:
- **Network Errors**: Connection issues with the API server
- **Authentication Errors**: Invalid credentials or expired tokens
- **Validation Errors**: Form validation with clear error messages
- **Server Errors**: Backend errors with user-friendly messages

## Testing

Authentication features are tested with:
- **Unit Tests**: Component and context testing
- **Integration Tests**: API integration testing
- **User Flow Tests**: Complete authentication flow testing

Run tests with:
```bash
# Activate virtual environment
.venv\Scripts\activate

# Run authentication tests
python -m pytest tests/test_auth_integration.py -v
```

## Future Enhancements

Potential improvements for the authentication system:
- **Social Login**: Integration with Google, GitHub, etc.
- **Two-Factor Authentication**: Additional security layer
- **Password Reset**: Email-based password reset functionality
- **Remember Me**: Extended session duration option
- **Admin Panel**: User management interface for administrators
