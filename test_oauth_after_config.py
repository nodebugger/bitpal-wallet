"""
Test Google OAuth Flow After Configuration
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("🧪 Testing Google OAuth Flow")
print("=" * 70)

# Test 1: Generate OAuth URL
print("\n1️⃣ Testing OAuth URL generation...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/auth/google?redirect=false")
    if response.status_code == 200:
        data = response.json()
        oauth_url = data.get("data", {}).get("google_auth_url")
        print(f"✅ OAuth URL generated successfully")
        print(f"   URL: {oauth_url[:80]}...")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Check redirect mode
print("\n2️⃣ Testing redirect mode...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/auth/google?redirect=true", allow_redirects=False)
    if response.status_code == 302:
        print(f"✅ Redirect works correctly")
        print(f"   Redirects to: {response.headers.get('location')[:80]}...")
    else:
        print(f"❌ Expected 302, got: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("📋 Next Steps:")
print("=" * 70)
print("""
1. ✅ CORS is now configured
2. ✅ Redirect URI updated to localhost

3. 🔴 YOU MUST ADD THIS TO GOOGLE CONSOLE:
   → Go to: https://console.cloud.google.com/apis/credentials
   → Click your OAuth 2.0 Client ID
   → Add to "Authorized redirect URIs":
      • http://localhost:8000/api/v1/auth/google/callback
      • http://127.0.0.1:8000/api/v1/auth/google/callback
   → Save and wait 1-2 minutes

4. After adding to Google Console, test the full flow:
   → Visit: http://localhost:8000/api/v1/auth/google
   → Sign in with Google
   → Should redirect back with success response
""")

print("=" * 70)
