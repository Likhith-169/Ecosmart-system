#!/usr/bin/env python3
"""
Simple test to verify fire detection consistency.
"""

import requests
import json
import time

def test_simple_consistency():
    """Test consistency with the same parameters."""
    
    # Same parameters for all tests
    params = {
        "bounds": [-122.5, 37.5, -122.0, 38.0],  # Small area
        "start_date": "2024-08-01",
        "end_date": "2024-08-07", 
        "satellite": "sentinel2",
        "max_cloud_cover": 40
    }
    
    print("🧪 Simple Consistency Test")
    print("=" * 40)
    print(f"Parameters: {json.dumps(params, indent=2)}")
    print()
    
    results = []
    
    # Run 3 tests
    for i in range(3):
        print(f"Test {i+1}/3: Starting detection...")
        
        try:
            # Start detection
            response = requests.post(
                "http://127.0.0.1:8000/api/v1/detect",
                json=params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                continue
                
            result = response.json()
            request_id = result["request_id"]
            
            # Wait for completion
            for _ in range(30):
                status_response = requests.get(f"http://127.0.0.1:8000/api/v1/status/{request_id}")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    
                    if status["status"] == "completed":
                        # Get results
                        results_response = requests.get(f"http://127.0.0.1:8000/api/v1/results/{request_id}")
                        
                        if results_response.status_code == 200:
                            final_results = results_response.json()
                            
                            test_result = {
                                "test": i + 1,
                                "events": final_results["summary"]["total_events"],
                                "area": round(final_results["summary"]["total_area_ha"], 2),
                                "confidence": round(final_results["summary"]["mean_confidence"], 3)
                            }
                            
                            results.append(test_result)
                            print(f"✅ Test {i+1}: {test_result['events']} events, {test_result['area']} ha")
                            break
                            
                        elif status["status"] == "failed":
                            print(f"❌ Test {i+1} failed")
                            break
                
                time.sleep(1)
            else:
                print(f"❌ Test {i+1} timed out")
                
        except Exception as e:
            print(f"❌ Test {i+1} error: {e}")
    
    print()
    print("📊 Results:")
    print("=" * 40)
    
    for result in results:
        print(f"Test {result['test']}: {result['events']} events, {result['area']} ha, {result['confidence']} conf")
    
    if len(results) >= 2:
        events = [r["events"] for r in results]
        areas = [r["area"] for r in results]
        confidences = [r["confidence"] for r in results]
        
        print()
        print("🔍 Consistency Check:")
        print(f"  Events: {events} - {'✅' if len(set(events)) == 1 else '❌'}")
        print(f"  Areas: {areas} - {'✅' if len(set(areas)) == 1 else '❌'}")
        print(f"  Confidences: {confidences} - {'✅' if len(set(confidences)) == 1 else '❌'}")
        
        consistent = len(set(events)) == 1 and len(set(areas)) == 1 and len(set(confidences)) == 1
        print()
        print("🎯 Overall: " + ("✅ CONSISTENT" if consistent else "❌ INCONSISTENT"))

if __name__ == "__main__":
    test_simple_consistency()
