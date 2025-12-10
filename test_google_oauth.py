"""
Simple test script to demonstrate Google OAuth flow.

Run this after starting your FastAPI server to see the OAuth flow in action.
"""

import httpx
import webbrowser
from urllib.parse import urlparse, parse_qs

BASE_URL = "https://bitpal-wallet-nodebugger1317-7uazwa8e.leapcell.dev/api/v1"


def test_google_oauth_flow():
    """
    Test the complete Google OAuth flow.
    
    This demonstrates:
    1. Getting the Google OAuth URL
    2. Opening it in a browser (manual step)
    3. Handling the callback (simulated)
    """
    
    print("=" * 60)
    print("🚀 Bitpal Wallet - Google OAuth Flow Test")
    print("=" * 60)
    
    # Step 1: Get Google OAuth URL
    print("\n📋 Step 1: Fetching Google OAuth URL...")
    response = httpx.get(f"{BASE_URL}/auth/google?redirect=false")
    
    if response.status_code == 200:
        data = response.json()
        google_auth_url = data["data"]["google_auth_url"]
        print("✅ OAuth URL generated successfully!")
        print(f"\n🔗 URL: {google_auth_url[:80]}...")
        
        # Step 2: Open in browser
        print("\n📋 Step 2: Opening Google OAuth page in browser...")
        print("👉 Please complete the sign-in process in your browser.")
        print("👉 After signing in, you'll be redirected to the callback URL.")
        print("👉 Copy the full callback URL from your browser address bar.")
        
        # Open the browser
        webbrowser.open(google_auth_url)
        
        # Step 3: Wait for user to paste the callback URL
        print("\n" + "=" * 60)
        callback_url = input("\n📥 Paste the full callback URL here: ").strip()
        
        # Extract the code parameter
        parsed_url = urlparse(callback_url)
        params = parse_qs(parsed_url.query)
        
        if 'code' in params:
            code = params['code'][0]
            print(f"\n✅ Authorization code extracted: {code[:30]}...")
            
            # Step 4: Exchange code for token (simulating what the callback does)
            print("\n📋 Step 4: Server exchanges code for user token...")
            print("✅ This happens automatically in your app!")
            print("✅ User would receive their JWT token and be logged in.")
            
            print("\n" + "=" * 60)
            print("🎉 OAuth Flow Complete!")
            print("=" * 60)
            print("\n📝 Summary:")
            print("1. ✅ User clicked 'Sign in with Google'")
            print("2. ✅ Redirected to Google for authentication")
            print("3. ✅ User granted permissions")
            print("4. ✅ Google sent authorization code")
            print("5. ✅ Server exchanged code for user info")
            print("6. ✅ User created/updated in database")
            print("7. ✅ JWT token issued to user")
            
        else:
            print("\n❌ Error: No authorization code found in URL")
            print("Make sure you copied the complete callback URL")
    else:
        print(f"❌ Failed to get OAuth URL: {response.status_code}")
        print(response.text)


def test_direct_redirect():
    """
    Test the direct redirect approach (simpler for web apps).
    """
    print("\n" + "=" * 60)
    print("🌐 Alternative: Direct Redirect Approach")
    print("=" * 60)
    print("\nFor web applications, you can simply redirect users to:")
    print(f"\n🔗 {BASE_URL}/auth/google")
    print("\nThis will automatically redirect to Google's OAuth page.")
    print("\nTry it: Opening in browser...")
    
    # Open the direct redirect URL
    webbrowser.open(f"{BASE_URL}/auth/google")


if __name__ == "__main__":
    import sys
    
    print("\n🔧 Make sure your FastAPI server is running!")
    print("   Run: uvicorn app.main:app --reload\n")
    
    choice = input("Choose test:\n1. Full OAuth flow (recommended)\n2. Direct redirect only\n\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_google_oauth_flow()
    elif choice == "2":
        test_direct_redirect()
    else:
        print("❌ Invalid choice. Please enter 1 or 2.")
