# Google OAuth Authentication Usage Guide

## Overview
The Bitpal Wallet Service uses **Google OAuth 2.0** for user authentication. This guide explains how to integrate the sign-in flow into your application.

---

## 🔄 Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant YourAPI
    participant Google
    participant Database

    User->>Frontend: Click "Sign in with Google"
    Frontend->>YourAPI: GET /api/v1/auth/google
    YourAPI->>Frontend: 302 Redirect to Google
    Frontend->>Google: Redirect to OAuth consent
    Google->>User: Show consent screen
    User->>Google: Grant permission
    Google->>YourAPI: GET /api/v1/auth/google/callback?code=xxx
    YourAPI->>Google: Exchange code for access token
    Google->>YourAPI: Return access token
    YourAPI->>Google: Fetch user info
    Google->>YourAPI: Return user details
    YourAPI->>Database: Create/Update user & wallet
    Database->>YourAPI: User saved
    YourAPI->>Frontend: Return JWT + user data
    Frontend->>User: Logged in successfully
```

---

## 📝 API Endpoints

### 1️⃣ **Trigger Google Sign-In Flow**

**Endpoint:** `GET /api/v1/auth/google`

**Purpose:** Initiates the OAuth flow by redirecting the user to Google's consent page.

#### **Usage Options:**

##### Option A: Browser/Web Frontend (Redirect)
```bash
# Simply navigate to this URL in the browser
http://localhost:8000/api/v1/auth/google
```

**Response:** 
- HTTP 302 redirect to Google OAuth consent page
- User will see Google's "Sign in with Google" screen

##### Option B: API/Mobile App (Get URL)
```bash
curl -X GET "http://localhost:8000/api/v1/auth/google?redirect=false"
```

**Response (JSON):**
```json
{
    "status_code": 200,
    "status": "success",
    "message": "Google OAuth URL generated",
    "data": {
        "google_auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=..."
    }
}
```

**Then:** Open `google_auth_url` in a webview or browser.

---

### 2️⃣ **Google OAuth Callback**

**Endpoint:** `GET /api/v1/auth/google/callback`

**Purpose:** Receives the authorization code from Google, exchanges it for user info, and returns a JWT token.

**⚠️ Note:** This endpoint is called by Google automatically after user consent. You don't call it directly.

#### **Query Parameters:**
- `code` (required): Authorization code sent by Google

#### **Success Response:**
```json
{
    "status_code": 200,
    "status": "success",
    "message": "Authentication successful",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer",
        "user": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "name": "John Doe",
            "wallet_number": "WAL123456789"
        }
    }
}
```

#### **Error Responses:**

**400 - Missing Code:**
```json
{
    "status_code": 400,
    "status": "error",
    "message": "Missing authorization code",
    "data": null
}
```

**401 - Invalid Code:**
```json
{
    "status_code": 401,
    "status": "error",
    "message": "Failed to exchange authorization code",
    "data": null
}
```

**500 - Server Error:**
```json
{
    "status_code": 500,
    "status": "error",
    "message": "Authentication failed",
    "data": null
}
```

---

## 💻 Frontend Integration Examples

### **React Example**

```jsx
import React from 'react';

function LoginPage() {
    const handleGoogleSignIn = () => {
        // Option 1: Direct redirect (simplest)
        window.location.href = 'http://localhost:8000/api/v1/auth/google';
        
        // Option 2: Get URL first, then redirect
        // fetch('http://localhost:8000/api/v1/auth/google?redirect=false')
        //     .then(res => res.json())
        //     .then(data => {
        //         window.location.href = data.data.google_auth_url;
        //     });
    };

    return (
        <div>
            <h1>Welcome to Bitpal Wallet</h1>
            <button onClick={handleGoogleSignIn}>
                <img src="/google-icon.png" alt="Google" />
                Sign in with Google
            </button>
        </div>
    );
}

export default LoginPage;
```

### **Vanilla JavaScript Example**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Bitpal Wallet - Login</title>
</head>
<body>
    <h1>Welcome to Bitpal Wallet</h1>
    <button onclick="signInWithGoogle()">Sign in with Google</button>

    <script>
        function signInWithGoogle() {
            // Simple redirect approach
            window.location.href = 'http://localhost:8000/api/v1/auth/google';
        }
    </script>
</body>
</html>
```

### **Mobile App (React Native / Flutter)**

```javascript
// React Native Example
import { Linking } from 'react-native';

const signInWithGoogle = async () => {
    try {
        // Get the OAuth URL
        const response = await fetch(
            'http://localhost:8000/api/v1/auth/google?redirect=false'
        );
        const data = await response.json();
        
        // Open in browser
        await Linking.openURL(data.data.google_auth_url);
        
        // Handle callback using deep linking
        // You'll need to set up a deep link handler to catch the redirect
    } catch (error) {
        console.error('Sign-in failed:', error);
    }
};
```

---

## 🔐 Using the JWT Token

After successful authentication, you'll receive a JWT token. Use it for all subsequent API requests:

### **Making Authenticated Requests**

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### **JavaScript Fetch Example**

```javascript
const token = localStorage.getItem('access_token');

fetch('http://localhost:8000/api/v1/users/me', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

---

## ⚙️ Configuration

### **Environment Variables (.env)**

```dotenv
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# For production
# GOOGLE_REDIRECT_URI=https://yourdomain.com/api/v1/auth/google/callback
```

### **Google Cloud Console Setup**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Add authorized redirect URIs:
   - Development: `http://localhost:8000/api/v1/auth/google/callback`
   - Production: `https://yourdomain.com/api/v1/auth/google/callback`
6. Copy **Client ID** and **Client Secret** to your `.env` file

---

## 🧪 Testing the Flow

### **1. Start the server:**
```bash
uvicorn app.main:app --reload
```

### **2. Open browser and visit:**
```
http://localhost:8000/api/v1/auth/google
```

### **3. Expected Flow:**
1. Redirects to Google login
2. You log in with your Google account
3. Google asks for consent (email, profile access)
4. You grant permission
5. Google redirects back to: `http://localhost:8000/api/v1/auth/google/callback?code=...`
6. You receive JSON response with JWT token and user info

### **4. Test with curl:**
```bash
# Step 1: Get the OAuth URL
curl -X GET "http://localhost:8000/api/v1/auth/google?redirect=false"

# Step 2: Copy the google_auth_url and open it in a browser
# Step 3: After consent, you'll be redirected to the callback with a token
```

---

## 🚨 Common Issues & Solutions

### **Issue: "Redirect URI mismatch"**
**Solution:** Make sure `GOOGLE_REDIRECT_URI` in `.env` exactly matches the URI in Google Cloud Console.

### **Issue: "Invalid client"**
**Solution:** Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct.

### **Issue: "Failed to exchange authorization code"**
**Solution:** 
- Check that `GOOGLE_CLIENT_SECRET` is correct
- Ensure the authorization code hasn't expired (valid for ~10 minutes)
- Verify your server's system time is correct

### **Issue: CORS errors in browser**
**Solution:** Add CORS middleware to your FastAPI app (already configured in your main.py).

---

## 📖 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI Authentication Guide](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - Decode and verify JWT tokens

---

## 🎯 Summary

**For users:** Just click "Sign in with Google" and grant permission.

**For developers:**
1. Frontend sends user to `GET /api/v1/auth/google`
2. Google handles authentication
3. Google redirects to `/api/v1/auth/google/callback` with code
4. Your server exchanges code for user info
5. Server creates user + wallet in database
6. Server returns JWT token to frontend
7. Frontend stores token and uses it for subsequent requests

**That's it! Simple and secure.** 🔒
