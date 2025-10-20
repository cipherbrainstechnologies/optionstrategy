#!/usr/bin/env python3
"""
Test script for manual scan functionality
"""
import requests
import time
import json

API_BASE = "http://localhost:8000"

def test_manual_scan():
    print("Testing Manual Scan Functionality")
    print("=" * 40)
    
    # Test 1: Check API health
    print("1. Testing API health...")
    try:
        response = requests.get(f"{API_BASE}/overview")
        if response.status_code == 200:
            print("✅ API is running")
            data = response.json()
            print(f"   Engine Status: {data.get('engineStatus')}")
            print(f"   Paper Mode: {data.get('paperMode')}")
        else:
            print("❌ API health check failed")
            return
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return
    
    # Test 2: Check scan status
    print("\n2. Checking scan status...")
    try:
        response = requests.get(f"{API_BASE}/scan/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Scan status: {status}")
        else:
            print("❌ Failed to get scan status")
    except Exception as e:
        print(f"❌ Scan status check failed: {e}")
    
    # Test 3: Trigger dry run scan
    print("\n3. Triggering dry run scan...")
    try:
        response = requests.post(
            f"{API_BASE}/scan",
            json={"dry_run": True},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Dry run scan started: {result}")
        else:
            print(f"❌ Dry run scan failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Dry run scan request failed: {e}")
        return
    
    # Test 4: Monitor scan progress
    print("\n4. Monitoring scan progress...")
    max_wait = 60  # 60 seconds max wait
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{API_BASE}/scan/status")
            if response.status_code == 200:
                status = response.json()
                print(f"   Status: {status}")
                
                if not status.get("running", False):
                    print("✅ Scan completed!")
                    if status.get("results"):
                        results = status["results"]
                        print(f"   Setups found: {len(results.get('setups', []))}")
                        print(f"   Breakouts found: {len(results.get('breakouts', []))}")
                        print(f"   Timestamp: {results.get('timestamp')}")
                    break
            else:
                print(f"❌ Status check failed: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ Status monitoring failed: {e}")
            break
        
        time.sleep(2)
    else:
        print("⏰ Scan monitoring timed out")
    
    print("\n" + "=" * 40)
    print("Manual scan test completed!")

if __name__ == "__main__":
    test_manual_scan()
