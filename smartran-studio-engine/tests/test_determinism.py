#!/usr/bin/env python3
"""
Test script to verify that Sionna simulation is deterministic.

This script tests:
1. Same tilts → Identical RSRP (determinism check)
2. Different tilts → Different RSRP (tilt sensitivity check)

Run this AFTER starting the FastAPI server (main.py).
"""

import requests
import json
import sys
from typing import Dict, List

BASE_URL = "http://localhost:8000"

def get_measurement_reports(threshold_dbm=-120.0):
    """Get measurement reports from the API"""
    response = requests.post(
        f"{BASE_URL}/measurement-reports",
        params={"threshold_dbm": threshold_dbm, "label_mode": "name"}
    )
    response.raise_for_status()
    return response.json()["measurement_reports"]

def compare_reports(reports1: List[Dict], reports2: List[Dict]) -> tuple:
    """
    Compare two sets of measurement reports.
    Returns (identical, num_diffs, max_diff_db, sample_diff)
    """
    if len(reports1) != len(reports2):
        return False, -1, -1, "Different number of users"
    
    num_diffs = 0
    max_diff_db = 0.0
    sample_diff = None
    
    for i, (r1, r2) in enumerate(zip(reports1, reports2)):
        if r1 != r2:
            num_diffs += 1
            if sample_diff is None:
                sample_diff = {
                    "user_idx": i,
                    "user_id": r1.get("user_id"),
                    "report1": r1,
                    "report2": r2
                }
                
            # Calculate max difference in RSRP values
            all_cells = set(r1.keys()) | set(r2.keys())
            all_cells.discard("user_id")
            for cell in all_cells:
                val1 = r1.get(cell, -140.0)
                val2 = r2.get(cell, -140.0)
                diff = abs(val1 - val2)
                max_diff_db = max(max_diff_db, diff)
    
    return (num_diffs == 0), num_diffs, max_diff_db, sample_diff

def test_determinism():
    """Test 1: Check if results are deterministic with same tilts"""
    print("=" * 70)
    print("TEST 1: DETERMINISM CHECK (same tilts should give identical RSRP)")
    print("=" * 70)
    
    print("\n🔄 Running first simulation...")
    reports1 = get_measurement_reports()
    
    print("🔄 Running second simulation (no changes)...")
    reports2 = get_measurement_reports()
    
    print("🔄 Running third simulation (triple check)...")
    reports3 = get_measurement_reports()
    
    # Compare run 1 vs run 2
    identical_12, diffs_12, max_diff_12, sample_12 = compare_reports(reports1, reports2)
    
    # Compare run 2 vs run 3
    identical_23, diffs_23, max_diff_23, sample_23 = compare_reports(reports2, reports3)
    
    print(f"\n📊 Results:")
    print(f"  Total users: {len(reports1)}")
    print(f"  Run 1 vs Run 2: {'✅ IDENTICAL' if identical_12 else f'❌ {diffs_12} users differ'}")
    if not identical_12:
        print(f"    Max RSRP difference: {max_diff_12:.4f} dB")
    print(f"  Run 2 vs Run 3: {'✅ IDENTICAL' if identical_23 else f'❌ {diffs_23} users differ'}")
    if not identical_23:
        print(f"    Max RSRP difference: {max_diff_23:.4f} dB")
    
    if identical_12 and identical_23:
        print("\n✅ PASS: Simulation is DETERMINISTIC!")
        print("   → Same tilts produce identical RSRP every time")
        print("   → Your optimization will see only tilt effects, not environment noise")
        return True
    else:
        print("\n❌ FAIL: Simulation has RANDOMNESS!")
        print("   → Results vary even with same tilts")
        print("   → This will confuse your optimization model")
        
        if sample_12:
            print(f"\n📝 Example difference (User {sample_12['user_idx']}):")
            print(f"   User ID: {sample_12['user_id']}")
            print(f"   Run 1: {len(sample_12['report1'])-1} cells above threshold")
            print(f"   Run 2: {len(sample_12['report2'])-1} cells above threshold")
        
        return False

def test_tilt_sensitivity():
    """Test 2: Check if tilt changes affect RSRP"""
    print("\n" + "=" * 70)
    print("TEST 2: TILT SENSITIVITY CHECK (tilt changes should affect RSRP)")
    print("=" * 70)
    
    print("\n🔄 Getting baseline RSRP...")
    reports_baseline = get_measurement_reports()
    
    # Get first cell info
    cells_response = requests.get(f"{BASE_URL}/cells")
    cells_response.raise_for_status()
    cells = cells_response.json()["cells"]
    
    if not cells:
        print("❌ No cells found!")
        return False
    
    first_cell = cells[0]
    original_tilt = first_cell["tilt_deg"]
    cell_name = first_cell["cell_name"]
    
    print(f"📡 Changing tilt of cell '{cell_name}' from {original_tilt}° to {original_tilt + 3.0}°")
    
    # Update tilt
    update_response = requests.post(
        f"{BASE_URL}/update-cell-tilts",
        json={"updates": [{"cell_id": 0, "tilt_deg": original_tilt + 3.0}]}
    )
    update_response.raise_for_status()
    
    print("🔄 Getting RSRP after tilt change...")
    reports_changed = get_measurement_reports()
    
    # Compare
    identical, num_diffs, max_diff, sample = compare_reports(reports_baseline, reports_changed)
    
    print(f"\n📊 Results:")
    print(f"  Users affected: {num_diffs} / {len(reports_baseline)}")
    print(f"  Max RSRP change: {max_diff:.4f} dB")
    
    if not identical and num_diffs > 0:
        print("\n✅ PASS: Tilt changes AFFECT RSRP!")
        print(f"   → {num_diffs} users saw RSRP changes")
        print(f"   → Maximum change: {max_diff:.2f} dB")
        print("   → Your optimization can learn from tilt adjustments")
        result = True
    else:
        print("\n❌ FAIL: Tilt changes have NO EFFECT!")
        print("   → This suggests a configuration problem")
        result = False
    
    # Restore original tilt
    print(f"\n🔧 Restoring original tilt ({original_tilt}°)...")
    requests.post(
        f"{BASE_URL}/update-cell-tilts",
        json={"updates": [{"cell_id": 0, "tilt_deg": original_tilt}]}
    )
    
    return result

def main():
    print("\n" + "🧪" * 35)
    print("  SIONNA DETERMINISM TEST SUITE")
    print("🧪" * 35)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        response.raise_for_status()
        print(f"\n✅ Server is running at {BASE_URL}")
        status = response.json()
        print(f"   Sites: {status['num_sites']}, Cells: {status['num_cells']}, UEs: {status['num_ues']}")
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to server at {BASE_URL}")
        print(f"   Make sure the FastAPI server is running (python main.py)")
        print(f"   Error: {e}")
        sys.exit(1)
    
    # Run tests
    test1_pass = test_determinism()
    test2_pass = test_tilt_sensitivity()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Test 1 (Determinism):      {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"  Test 2 (Tilt Sensitivity): {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if test1_pass and test2_pass:
        print("\n🎉 ALL TESTS PASSED!")
        print("   Your environment is FROZEN and ready for optimization!")
        print("   Only tilt changes will affect RSRP measurements.")
    else:
        print("\n⚠️  SOME TESTS FAILED!")
        if not test1_pass:
            print("   → Environment is NOT deterministic (shadow fading enabled?)")
            print("   → Try disabling shadow fading: enable_shadow_fading=False")
        if not test2_pass:
            print("   → Tilt changes don't affect RSRP (configuration issue?)")
    
    print("\n" + "=" * 70)
    
    return 0 if (test1_pass and test2_pass) else 1

if __name__ == "__main__":
    sys.exit(main())

