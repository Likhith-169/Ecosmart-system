#!/usr/bin/env python3
"""
Test the new deterministic hash function.
"""

def test_hash_function():
    """Test if the new hash function is deterministic."""
    
    # Same parameters
    bounds = [-122.5, 37.5, -122.0, 38.0]
    start_date = "2024-08-01"
    end_date = "2024-08-07"
    satellite = "sentinel2"
    max_cloud_cover = 40
    
    print("🔍 Testing New Hash Function")
    print("=" * 40)
    print(f"Bounds: {bounds}")
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")
    print(f"Satellite: {satellite}")
    print(f"Max Cloud Cover: {max_cloud_cover}")
    print()
    
    # Test seed calculation 5 times
    for i in range(5):
        # Calculate seed using the new method
        seed_string = f"{bounds}_{start_date}_{end_date}_{satellite}_{max_cloud_cover}"
        
        # Simple but reliable deterministic hash
        seed = 0
        for char in seed_string:
            seed = ((seed << 5) + seed + ord(char)) & 0xFFFFFFFF
        seed = seed % (2**32)  # Ensure positive seed
        
        print(f"Test {i+1}: Seed = {seed}")
        
        # Also test area size calculation
        area_size = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
        
        # Simple but reliable deterministic hash for area
        area_hash = 0
        for char in str(area_size):
            area_hash = ((area_hash << 5) + area_hash + ord(char)) & 0xFFFFFFFF
        area_hash = area_hash % 1000
        
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
    test_hash_function()
