"""
Test script for ISL Sign Language Backend API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health Check Response:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_stats():
    """Test the stats endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print("\nStats Response:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Stats check failed: {e}")
        return False

def test_text_to_sign():
    """Test text to sign language conversion"""
    try:
        data = {
            "text": "hello world",
            "speed": 1.0
        }
        response = requests.post(f"{BASE_URL}/text-to-sign", json=data)
        print("\nText-to-Sign Response:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Text-to-sign test failed: {e}")
        return False

def test_root():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print("\nRoot Response:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Root test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing ISL Sign Language Backend API")
    print("=" * 50)
    
    # Test all endpoints
    tests = [
        ("Root Endpoint", test_root),
        ("Health Check", test_health_check),
        ("Stats", test_stats),
        ("Text-to-Sign", test_text_to_sign)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        success = test_func()
        results.append((test_name, success))
        print(f"✅ {test_name}: {'PASSED' if success else 'FAILED'}")
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your API is working correctly!")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")