#!/usr/bin/env python3
"""
Test script to verify consistency of fire detection results.
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_consistency():
    """Test that the same input parameters produce consistent results."""
    
    # Test parameters - same for all tests
    test_params = {
        "bounds": [-124.5, 32.5, -114.0, 42.0],  # California
        "start_date": "2024-08-01",
        "end_date": "2024-08-07",
        "satellite": "sentinel2",
        "max_cloud_cover": 40
    }
    
    print("🧪 Testing Fire Detection Consistency")
    print("=" * 50)
    print(f"Test Parameters: {json.dumps(test_params, indent=2)}")
    print()
    
    results = []
    
    # Run 5 tests with the same parameters
    for i in range(5):
        print(f"Test {i+1}/5: Starting detection...")
        
        try:
            # Start detection
            response = requests.post(
                "http://127.0.0.1:8000/api/v1/detect",
                json=test_params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Error starting detection: {response.status_code}")
                continue
                
            result = response.json()
            request_id = result["request_id"]
            
            # Poll for results
            max_attempts = 30
            for attempt in range(max_attempts):
                status_response = requests.get(f"http://127.0.0.1:8000/api/v1/status/{request_id}")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    
                    if status["status"] == "completed":
                        # Get final results
                        results_response = requests.get(f"http://127.0.0.1:8000/api/v1/results/{request_id}")
                        
                        if results_response.status_code == 200:
                            final_results = results_response.json()
                            
                            # Extract key metrics
                            test_result = {
                                "test_number": i + 1,
                                "total_events": final_results["summary"]["total_events"],
                                "total_area_ha": final_results["summary"]["total_area_ha"],
                                "mean_confidence": final_results["summary"]["mean_confidence"],
                                "seed": final_results.get("metadata", {}).get("seed", "N/A"),
                                "processing_time": final_results.get("metadata", {}).get("processing_time", 0)
                            }
                            
                            results.append(test_result)
                            print(f"✅ Test {i+1} completed: {test_result['total_events']} events, Seed: {test_result['seed']}")
                            break
                            
                        elif status["status"] == "failed":
                            print(f"❌ Test {i+1} failed: {status.get('error', 'Unknown error')}")
                            break
                
                time.sleep(1)
            else:
                print(f"❌ Test {i+1} timed out")
                
        except Exception as e:
            print(f"❌ Test {i+1} error: {e}")
    
    print()
    print("📊 Consistency Test Results")
    print("=" * 50)
    
    if len(results) < 2:
        print("❌ Not enough successful tests to analyze consistency")
        return
    
    # Analyze consistency
    events = [r["total_events"] for r in results]
    areas = [r["total_area_ha"] for r in results]
    confidences = [r["mean_confidence"] for r in results]
    seeds = [r["seed"] for r in results]
    
    print(f"Total Events: {events}")
    print(f"Total Areas: {[round(a, 2) for a in areas]}")
    print(f"Mean Confidences: {[round(c, 3) for c in confidences]}")
    print(f"Seeds: {seeds}")
    print()
    
    # Check consistency
    events_consistent = len(set(events)) == 1
    areas_consistent = len(set([round(a, 2) for a in areas])) == 1
    confidences_consistent = len(set([round(c, 3) for c in confidences])) == 1
    seeds_consistent = len(set(seeds)) == 1
    
    print("🔍 Consistency Analysis:")
    print(f"  Events consistent: {'✅' if events_consistent else '❌'}")
    print(f"  Areas consistent: {'✅' if areas_consistent else '❌'}")
    print(f"  Confidences consistent: {'✅' if confidences_consistent else '❌'}")
    print(f"  Seeds consistent: {'✅' if seeds_consistent else '❌'}")
    
    overall_consistent = events_consistent and areas_consistent and confidences_consistent and seeds_consistent
    
    print()
    if overall_consistent:
        print("🎉 All tests produced consistent results!")
    else:
        print("⚠️  Inconsistencies detected in results")
    
    return overall_consistent

if __name__ == "__main__":
    test_consistency()
