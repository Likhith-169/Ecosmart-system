#!/usr/bin/env python3
"""
Detailed test to analyze what's causing inconsistencies.
"""

import requests
import json
import time

def test_detailed_consistency():
    """Test with detailed analysis of each detection."""
    
    # Same parameters
    params = {
        "bounds": [-122.5, 37.5, -122.0, 38.0],
        "start_date": "2024-08-01",
        "end_date": "2024-08-07",
        "satellite": "sentinel2",
        "max_cloud_cover": 40
    }
    
    print("🔍 Detailed Consistency Analysis")
    print("=" * 50)
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
                            
                            # Extract detailed information
                            detections = final_results.get("detections", [])
                            test_result = {
                                "test": i + 1,
                                "total_events": final_results["summary"]["total_events"],
                                "total_area_ha": round(final_results["summary"]["total_area_ha"], 2),
                                "mean_confidence": round(final_results["summary"]["mean_confidence"], 3),
                                "detection_details": []
                            }
                            
                            for j, detection in enumerate(detections):
                                test_result["detection_details"].append({
                                    "id": detection["id"],
                                    "area_ha": round(detection["area_ha"], 2),
                                    "confidence": round(detection["confidence"], 3),
                                    "location": detection["location"],
                                    "coordinates": detection["geometry"]["coordinates"][0][0]  # First coordinate
                                })
                            
                            results.append(test_result)
                            print(f"✅ Test {i+1}: {test_result['total_events']} events, {test_result['total_area_ha']} ha")
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
    print("📊 Detailed Results:")
    print("=" * 50)
    
    for result in results:
        print(f"\nTest {result['test']}:")
        print(f"  Total Events: {result['total_events']}")
        print(f"  Total Area: {result['total_area_ha']} ha")
        print(f"  Mean Confidence: {result['mean_confidence']}")
        print(f"  Detections:")
        for det in result['detection_details']:
            print(f"    - {det['id']}: {det['area_ha']} ha, {det['confidence']} conf, {det['location']}")
            print(f"      Coords: {det['coordinates']}")
    
    # Analyze differences
    if len(results) >= 2:
        print("\n🔍 Analysis:")
        print("=" * 50)
        
        # Check if number of events is consistent
        events = [r["total_events"] for r in results]
        print(f"Number of events: {events}")
        print(f"Events consistent: {'✅' if len(set(events)) == 1 else '❌'}")
        
        # Check if areas are consistent
        areas = [r["total_area_ha"] for r in results]
        print(f"Total areas: {areas}")
        print(f"Areas consistent: {'✅' if len(set(areas)) == 1 else '❌'}")
        
        # Check if detection IDs are consistent
        all_ids = [det["id"] for r in results for det in r["detection_details"]]
        print(f"Detection IDs: {all_ids}")
        print(f"IDs consistent: {'✅' if len(set(all_ids)) == len(all_ids) else '❌'}")

if __name__ == "__main__":
    test_detailed_consistency()
