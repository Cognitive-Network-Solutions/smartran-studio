#!/usr/bin/env python3
"""
Round-trip determinism test: Change tilts and return to original, verify same RSRP
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_measurement_reports():
    """Get measurement reports"""
    response = requests.post(
        f"{BASE_URL}/measurement-reports",
        params={"threshold_dbm": -120.0, "label_mode": "name"}
    )
    response.raise_for_status()
    return response.json()["measurement_reports"]

def get_cell_tilts():
    """Get current cell tilts"""
    response = requests.get(f"{BASE_URL}/cells")
    response.raise_for_status()
    cells = response.json()["cells"]
    return [(c["cell_idx"], c["cell_name"], c["tilt_deg"]) for c in cells]

def update_tilt(cell_id, new_tilt):
    """Update a single cell's tilt"""
    response = requests.post(
        f"{BASE_URL}/update-cell-tilts",
        json={"updates": [{"cell_id": cell_id, "tilt_deg": new_tilt}]}
    )
    response.raise_for_status()
    return response.json()

def compare_reports(r1, r2, label=""):
    """Compare two report sets"""
    if r1 == r2:
        print(f"  ✅ {label}: Reports are IDENTICAL")
        return True
    else:
        print(f"  ❌ {label}: Reports DIFFER")
        # Show first difference
        for i, (u1, u2) in enumerate(zip(r1, r2)):
            if u1 != u2:
                print(f"     First diff at user {i} ({u1['user_id']}):")
                cells1 = set(u1.keys()) - {"user_id"}
                cells2 = set(u2.keys()) - {"user_id"}
                if cells1 != cells2:
                    print(f"       Different cells detected")
                else:
                    for cell in cells1:
                        if u1[cell] != u2[cell]:
                            print(f"       {cell}: {u1[cell]:.10f} vs {u2[cell]:.10f}")
                            break
                break
        return False

print("=" * 70)
print("ROUND-TRIP TILT DETERMINISM TEST")
print("=" * 70)
print("\nTest: tilt=6° → tilt=8° → tilt=6° (should return to original RSRP)")

# Clear cache and get initial state
print("\n🔄 Step 0: Clearing cache...")
requests.post(f"{BASE_URL}/clear-cache")

# Get first cell info
tilts = get_cell_tilts()
test_cell = tilts[0]
cell_id, cell_name, original_tilt = test_cell
print(f"\n📡 Test cell: {cell_name} (ID: {cell_id})")
print(f"   Original tilt: {original_tilt}°")

# Step 1: Baseline with tilt=6° (or whatever original is)
print(f"\n{'='*70}")
print(f"STEP 1: Baseline measurement at tilt={original_tilt}°")
print(f"{'='*70}")
reports_1 = get_measurement_reports()
print(f"✅ Got {len(reports_1)} reports")
print(f"   User 0 sample: {list(reports_1[0].items())[:3]}")

# Step 2: Change to different tilt (e.g., +3°)
new_tilt = original_tilt + 3.0
print(f"\n{'='*70}")
print(f"STEP 2: Change {cell_name} tilt to {new_tilt}°")
print(f"{'='*70}")
update_result = update_tilt(cell_id, new_tilt)
print(f"✅ Tilt updated: {original_tilt}° → {new_tilt}°")

reports_2 = get_measurement_reports()
print(f"✅ Got {len(reports_2)} reports")

# Verify it's different
if reports_1 != reports_2:
    print(f"✅ RSRP changed (as expected when tilt changes)")
else:
    print(f"⚠️  WARNING: RSRP didn't change (unexpected!)")

# Step 3: Change back to original tilt
print(f"\n{'='*70}")
print(f"STEP 3: Change {cell_name} tilt BACK to {original_tilt}°")
print(f"{'='*70}")
update_result = update_tilt(cell_id, original_tilt)
print(f"✅ Tilt restored: {new_tilt}° → {original_tilt}°")

reports_3 = get_measurement_reports()
print(f"✅ Got {len(reports_3)} reports")

# Step 4: Critical comparison - Should match Step 1!
print(f"\n{'='*70}")
print(f"STEP 4: CRITICAL TEST - Compare Step 1 vs Step 3")
print(f"{'='*70}")
print(f"\nBoth measurements at tilt={original_tilt}°:")
print(f"  Step 1: Initial baseline")
print(f"  Step 3: After round-trip (6→8→6)")

if reports_1 == reports_3:
    print(f"\n✅✅✅ SUCCESS! ✅✅✅")
    print(f"\nRound-trip returned to IDENTICAL RSRP!")
    print(f"  • Same tilt → Same RSRP (even after changing)")
    print(f"  • Cache correctly handles tilt changes")
    print(f"  • Your optimization will see consistent results")
    
    # Show detailed comparison for first user
    print(f"\n📊 Detailed verification (User 0):")
    cells_1 = {k: v for k, v in reports_1[0].items() if k != "user_id"}
    cells_3 = {k: v for k, v in reports_3[0].items() if k != "user_id"}
    
    for cell in list(cells_1.keys())[:3]:
        print(f"  {cell}:")
        print(f"    Step 1: {cells_1[cell]:.10f} dBm")
        print(f"    Step 3: {cells_3[cell]:.10f} dBm")
        print(f"    Match: {'✅' if cells_1[cell] == cells_3[cell] else '❌'}")
    
else:
    print(f"\n❌❌❌ FAILURE! ❌❌❌")
    print(f"\nRound-trip did NOT return to original RSRP!")
    print(f"  • This means cache is NOT preserving history")
    print(f"  • Same tilt gives DIFFERENT RSRP after changes")
    print(f"  • This is a PROBLEM for optimization!")
    
    print(f"\n📊 First user comparison:")
    print(f"  User ID: {reports_1[0]['user_id']}")
    print(f"  Step 1 cells: {len(reports_1[0])-1}")
    print(f"  Step 3 cells: {len(reports_3[0])-1}")
    
    # Show sample differences
    cells_1 = {k: v for k, v in reports_1[0].items() if k != "user_id"}
    cells_3 = {k: v for k, v in reports_3[0].items() if k != "user_id"}
    
    common_cells = set(cells_1.keys()) & set(cells_3.keys())
    for cell in list(common_cells)[:3]:
        diff = abs(cells_1[cell] - cells_3[cell])
        print(f"\n  {cell}:")
        print(f"    Step 1: {cells_1[cell]:.10f} dBm")
        print(f"    Step 3: {cells_3[cell]:.10f} dBm")
        print(f"    Diff: {diff:.10f} dB")

# Step 5: Extra verification - repeat Step 3
print(f"\n{'='*70}")
print(f"STEP 5: Extra verification - call again (no tilt change)")
print(f"{'='*70}")
reports_4 = get_measurement_reports()

if reports_3 == reports_4:
    print(f"✅ Step 3 == Step 4 (cache working within same tilt)")
else:
    print(f"❌ Step 3 != Step 4 (cache broken!)")

print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")
print(f"\nTilt sequence: {original_tilt}° → {new_tilt}° → {original_tilt}°")
print(f"\nResults:")
print(f"  Step 1 vs Step 2 (different tilts): {'Different ✅' if reports_1 != reports_2 else 'Same ❌'}")
print(f"  Step 1 vs Step 3 (same tilt):       {'Same ✅' if reports_1 == reports_3 else 'Different ❌'}")
print(f"  Step 3 vs Step 4 (no change):       {'Same ✅' if reports_3 == reports_4 else 'Different ❌'}")

if reports_1 == reports_3 and reports_3 == reports_4:
    print(f"\n🎉 ALL TESTS PASSED! Round-trip determinism confirmed!")
else:
    print(f"\n⚠️  ISSUE DETECTED: Cache may need multi-state memory")

print(f"\n{'='*70}")

