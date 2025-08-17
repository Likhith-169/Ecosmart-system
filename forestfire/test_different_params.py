#!/usr/bin/env python3
"""
Test consistency with different parameters.
"""

import requests
import json
import time

def test_different_parameters():
    """Test consistency with different parameter sets."""
    
    test_cases = [
        {
            "name": "California Small Area",
            "params": {
                "bounds": [-122.5, 37.5, -122.0, 38.0],
                "start_date": "2024-08-01",
                "end_date": "2024-08-07",
                "satellite": "sentinel2",
                "max_cloud_cover": 40
            }
        },
        {
            "name": "California Large Area",
            "params": {
                "bounds": [-124.5, 32.5, -114.0, 42.0],
                "start_date": "2024-08-01",
                "end_date": "2024-08-07",
                "satellite": "sentinel2",
                "max_cloud_cover": 40
            }
        },
        {
            "name": "Australia Area",
            "params": {
                "bounds": [145.0, -37.5, 150.0, -33.0],
                "start_date": "2024-08-01",
                "end_date": "2024-08-07",
                "satellite": "landsat",
                "max_cloud_cover": 30
            }
        }
    ]
    
    print("🧪 Testing Consistency with Different Parameters")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print("-" * 40)
        print(f"Parameters: {json.dumps(test_case['params'], indent=2)}")
        
        results = []
        
        # Run 2 tests for each case
        for i in range(2):
            print(f"  Test {i+1}/2: Starting detection...")
            
            try:
                # Start detection
                response = requests.post(
                    "http://127.0.0.1:8000/api/v1/detect",
                    json=test_case['params'],
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"    ❌ Error: {response.status_code}")
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
                                print(f"    ✅ Test {i+1}: {test_result['events']} events, {test_result['area']} ha")
                                break
                                
                            elif status["status"] == "failed":
                                print(f"    ❌ Test {i+1} failed")
                                break
                    
                    time.sleep(1)
                else:
                    print(f"    ❌ Test {i+1} timed out")
                    
            except Exception as e:
                print(f"    ❌ Test {i+1} error: {e}")
        
        # Check consistency for this test case
        if len(results) >= 2:
            events = [r["events"] for r in results]
            areas = [r["area"] for r in results]
            confidences = [r["confidence"] for r in results]
            
            events_consistent = len(set(events)) == 1
            areas_consistent = len(set(areas)) == 1
            confidences_consistent = len(set(confidences)) == 1
            
            print(f"  📊 Results: {events} events, {areas} ha, {confidences} conf")
            print(f"  🔍 Consistency: Events {'✅' if events_consistent else '❌'}, Areas {'✅' if areas_consistent else '❌'}, Confidences {'✅' if confidences_consistent else '❌'}")
            
            overall_consistent = events_consistent and areas_consistent and confidences_consistent
            print(f"  🎯 Overall: {'✅ CONSISTENT' if overall_consistent else '❌ INCONSISTENT'}")
        else:
            print(f"  ❌ Not enough results to check consistency")

if __name__ == "__main__":
    test_different_parameters()
