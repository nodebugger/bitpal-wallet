"""
Quick OAuth Test - After Foreign Key Fix
"""
print("=" * 70)
print("🧪 Testing OAuth Flow After Foreign Key Fix")
print("=" * 70)
print("""
The SQLAlchemy relationship error has been fixed!

Now test the OAuth flow:

1. Visit: http://localhost:8000/api/v1/auth/google

2. Sign in with your Google account

3. You should now see a SUCCESS response like:
   {
     "status_code": 200,
     "status": "success",
     "message": "Authentication successful",
     "data": {
       "access_token": "eyJ0eXAiOiJKV1QiLCJh...",
       "token_type": "bearer",
       "user": {
         "id": "uuid-here",
         "email": "your@email.com",
         "name": "Your Name",
         "wallet_number": "1234567890123"
       }
     }
   }

4. Copy the access_token for testing other endpoints!
""")
print("=" * 70)
print("📝 To test with the token:")
print("=" * 70)
print("""
# Get wallet balance:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/wallet/balance

# Create API key:
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"name":"My API Key","permissions":["deposit","transfer","read"],"expiry":"1M"}' \\
  http://localhost:8000/api/v1/keys/create
""")
print("=" * 70)
