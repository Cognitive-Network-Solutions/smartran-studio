#!/usr/bin/env python3
"""
Manual determinism test: Run multiple times with same tilts and compare exact RSRP values
"""

import requests
import json
import hashlib

BASE_URL = "http://localhost:8000"

def get_measurement_reports():
    """Get measurement reports"""
    response = requests.post(
        f"{BASE_URL}/measurement-reports",
        params={"threshold_dbm": -120.0, "label_mode": "name"}
    )
    response.raise_for_status()
    return response.json()["measurement_reports"]

def hash_reports(reports):
    """Create a hash of the reports for easy comparison"""
    # Sort and serialize to ensure consistent ordering
    serialized = json.dumps(reports, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()

def print_sample_data(reports, run_number):
    """Print sample data from first few users"""
    print(f"\n📊 Run {run_number} - Sample Data (first 3 users):")
    for i in range(min(3, len(reports))):
        user_id = reports[i].get("user_id")
        cells = {k: v for k, v in reports[i].items() if k != "user_id"}
        print(f"  {user_id}: {len(cells)} cells, sample RSRP values:")
        # Show first 3 cell values
        for j, (cell, rsrp) in enumerate(list(cells.items())[:3]):
            print(f"    {cell}: {rsrp:.6f} dBm")

print("=" * 70)
print("MANUAL DETERMINISM TEST")
print("=" * 70)

# Clear cache to start fresh
print("\n🔄 Clearing cache...")
requests.post(f"{BASE_URL}/clear-cache")

# Get current tilts
cells_response = requests.get(f"{BASE_URL}/cells")
cells = cells_response.json()["cells"]
print(f"✅ Current configuration: {len(cells)} cells")
print(f"   Sample tilts: {[c['tilt_deg'] for c in cells[:5]]}")

# Run multiple times
num_runs = 5
all_reports = []
all_hashes = []

print(f"\n🔄 Running {num_runs} simulations with IDENTICAL tilts...\n")

for i in range(1, num_runs + 1):
    print(f"Run {i}...")
    reports = get_measurement_reports()
    all_reports.append(reports)
    
    # Calculate hash
    report_hash = hash_reports(reports)
    all_hashes.append(report_hash)
    
    # Print summary
    print(f"  ✅ Got {len(reports)} user reports")
    print(f"  Hash: {report_hash[:16]}...")
    
    # Print detailed data for first run
    if i == 1:
        print_sample_data(reports, i)

# Compare all runs
print("\n" + "=" * 70)
print("COMPARISON RESULTS")
print("=" * 70)

# Check if all hashes are identical
all_identical = len(set(all_hashes)) == 1

if all_identical:
    print("\n✅ ✅ ✅ SUCCESS! ALL RUNS ARE IDENTICAL! ✅ ✅ ✅")
    print(f"\n   All {num_runs} runs produced the EXACT SAME data")
    print(f"   Hash: {all_hashes[0]}")
    print("\n   This means:")
    print("   • Environment is completely FROZEN")
    print("   • No randomness between calls")
    print("   • Perfect reproducibility for your AI model")
else:
    print("\n❌ FAILURE: Runs produced DIFFERENT data")
    print("\n   Unique hashes found:")
    for idx, h in enumerate(set(all_hashes), 1):
        count = all_hashes.count(h)
        print(f"   {idx}. {h} (appeared {count} time(s))")

# Detailed comparison of first user across all runs
print("\n" + "=" * 70)
print("DETAILED COMPARISON: First User Across All Runs")
print("=" * 70)

user0_data = []
for i, reports in enumerate(all_reports, 1):
    user0 = reports[0]
    user0_data.append(user0)
    print(f"\nRun {i} - {user0['user_id']}:")
    cells = {k: v for k, v in user0.items() if k != "user_id"}
    print(f"  Total cells: {len(cells)}")
    # Show first 5 cells with exact values
    for cell, rsrp in list(cells.items())[:5]:
        print(f"  {cell}: {rsrp:.10f} dBm")

# Check if user0 data is identical
if all(user0_data[0] == data for data in user0_data):
    print(f"\n✅ First user data is IDENTICAL across all {num_runs} runs!")
else:
    print(f"\n❌ First user data DIFFERS between runs")
    # Find differences
    for i in range(1, len(user0_data)):
        if user0_data[0] != user0_data[i]:
            print(f"\n   Difference found between Run 1 and Run {i+1}:")
            cells_0 = set(user0_data[0].keys())
            cells_i = set(user0_data[i].keys())
            if cells_0 != cells_i:
                print(f"   - Different cells detected")
                print(f"     Only in Run 1: {cells_0 - cells_i}")
                print(f"     Only in Run {i+1}: {cells_i - cells_0}")
            else:
                # Same cells, different values
                for cell in cells_0:
                    if cell != "user_id":
                        val_0 = user0_data[0][cell]
                        val_i = user0_data[i][cell]
                        if val_0 != val_i:
                            print(f"   - {cell}: {val_0:.10f} vs {val_i:.10f} (diff: {abs(val_0-val_i):.10f} dB)")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

