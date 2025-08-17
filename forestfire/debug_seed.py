#!/usr/bin/env python3
"""
Debug script to test seed calculation consistency.
"""

def test_seed_calculation():
    """Test if the same parameters produce the same seed."""
    
    # Same parameters
    bounds = [-122.5, 37.5, -122.0, 38.0]
    start_date = "2024-08-01"
    end_date = "2024-08-07"
    satellite = "sentinel2"
    max_cloud_cover = 40
    
    print("🔍 Testing Seed Calculation")
    print("=" * 40)
    print(f"Bounds: {bounds}")
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")
    print(f"Satellite: {satellite}")
    print(f"Max Cloud Cover: {max_cloud_cover}")
    print()
    
    # Test seed calculation 5 times
    for i in range(5):
        # Calculate seed the same way as in the API
        seed_string = f"{bounds}_{start_date}_{end_date}_{satellite}_{max_cloud_cover}"
        seed = hash(seed_string) % (2**32)
        
        print(f"Test {i+1}: Seed = {seed}")
        
        # Also test area size calculation
        area_size = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
        area_hash = int(abs(hash(str(area_size))) % 1000)
        seed_mod = seed % 1000
        combined_value = (area_hash + seed_mod) % 1000
        
        print(f"  Area size: {area_size}")
        print(f"  Area hash: {area_hash}")
        print(f"  Seed mod: {seed_mod}")
        print(f"  Combined value: {combined_value}")
        
        # Map to number of detections
        if combined_value < 200:
            num_detections = 0
        elif combined_value < 400:
            num_detections = 1
        elif combined_value < 600:
            num_detections = 2
        elif combined_value < 800:
            num_detections = 3
        else:
            num_detections = 4
        
        print(f"  Number of detections: {num_detections}")
        print()

if __name__ == "__main__":
    test_seed_calculation()
