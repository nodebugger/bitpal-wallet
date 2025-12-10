"""
Quick Google OAuth Configuration Checker
"""
from app.core.config import settings

print("=" * 60)
print("🔍 Google OAuth Configuration Check")
print("=" * 60)

print(f"\n✅ Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")
print(f"✅ Client Secret: {settings.GOOGLE_CLIENT_SECRET[:10]}...")
print(f"✅ Redirect URI: {settings.GOOGLE_REDIRECT_URI}")

print("\n" + "=" * 60)
print("📋 Google Cloud Console Setup Instructions")
print("=" * 60)

print("""
1. Go to: https://console.cloud.google.com/apis/credentials

2. Click on your OAuth 2.0 Client ID

3. In "Authorized redirect URIs", add:
   ✅ http://localhost:8000/api/v1/auth/google/callback
   ✅ http://127.0.0.1:8000/api/v1/auth/google/callback
   
   (Also keep your production URL if deployed)

4. Click "Save"

5. Wait 1-2 minutes for changes to propagate

6. Test the OAuth flow again
""")

print("=" * 60)
print("🧪 Testing OAuth Flow")
print("=" * 60)
print(f"""
1. Visit: http://localhost:8000/api/v1/auth/google?redirect=false
2. Copy the google_auth_url from the response
3. Open the URL in your browser
4. Sign in with Google
5. You should be redirected back to localhost with a success response
""")
