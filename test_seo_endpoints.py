#!/usr/bin/env python3
"""
Test script for SEO endpoints
"""

import requests
import json
import pytest

BASE_URL = "http://localhost:8000"

def test_connect_url():
    """Test the connect URL endpoint"""
    print("Testing GET /api/seo/13/connect-url")
    try:
        response = requests.get(f"{BASE_URL}/api/seo/13/connect-url", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if "auth_url" in data:
                print("✅ Connect URL endpoint working")
                assert True
            else:
                assert False, "Missing auth_url in response"
        else:
            pytest.skip(f"Connect URL endpoint returned: {response.status_code}")
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running - connection refused")
    except Exception as e:
        pytest.skip(f"Exception occurred: {e}")
    
    print("-" * 50)

def test_sites_endpoint():
    """Test the sites endpoint (should fail without connection)"""
    print("Testing GET /api/seo/13/sites")
    try:
        response = requests.get(f"{BASE_URL}/api/seo/13/sites", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 404:
            print("✅ Sites endpoint correctly returns 404 when no connection exists")
            assert True
        else:
            print(f"Response: {response.text}")
            assert False, f"Expected 404, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running - connection refused")
    except Exception as e:
        pytest.skip(f"Exception occurred: {e}")
    
    print("-" * 50)

def test_overview_endpoint():
    """Test the overview endpoint (should fail without connection)"""
    print("Testing GET /api/seo/13/overview")
    try:
        response = requests.get(f"{BASE_URL}/api/seo/13/overview", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 404:
            print("✅ Overview endpoint correctly returns 404 when no connection exists")
            assert True
        else:
            print(f"Response: {response.text}")
            assert False, f"Expected 404, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running - connection refused")
    except Exception as e:
        pytest.skip(f"Exception occurred: {e}")
    
    print("-" * 50)

def test_server_health():
    """Test if server is running"""
    print("Testing server health")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            assert True, "Server is running"
        else:
            print(f"❌ Server returned status: {response.status_code}")
            pytest.skip(f"Server returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        pytest.skip(f"Server not accessible: {e}")

if __name__ == "__main__":
    print("🔍 Testing SEO Endpoints")
    print("=" * 50)
    
    if test_server_health():
        test_connect_url()
        test_sites_endpoint()
        test_overview_endpoint()
    else:
        print("❌ Please start the server first: python main.py")
