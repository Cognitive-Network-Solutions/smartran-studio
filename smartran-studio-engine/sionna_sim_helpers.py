import numpy as np
import random
import math


def add_site_with_dualband_cells(
    sim,
    *,
    site_name: str,
    x: float,
    y: float,
    height_m: float = 25.0,
    az0_deg: float = 0.0,
    uid: str | None = None,
    # high band RF params
    fc_hi_hz: float = 25_002e6, band_hi: str = "H", tilt_hi_deg: float = 6.0, pwr_hi_dbm: float = 0.0,
    # low band RF params
    fc_lo_hz: float = 600e6,    band_lo: str = "L", tilt_lo_deg: float = 3.0, pwr_lo_dbm: float = 0.0,
    # high band antenna config (None = use sim defaults from arr_cfg)
    bs_rows_hi: int | None = None,
    bs_cols_hi: int | None = None,
    bs_pol_hi: str | None = None,
    bs_pol_type_hi: str | None = None,
    elem_v_spacing_hi: float | None = None,
    elem_h_spacing_hi: float | None = None,
    antenna_pattern_hi: str | None = None,
    # low band antenna config (None = use sim defaults from arr_cfg)
    bs_rows_lo: int | None = None,
    bs_cols_lo: int | None = None,
    bs_pol_lo: str | None = None,
    bs_pol_type_lo: str | None = None,
    elem_v_spacing_lo: float | None = None,
    elem_h_spacing_lo: float | None = None,
    antenna_pattern_lo: str | None = None,
    # control carrier block order (affects column grouping in RSRP_dBm)
    order: str = "hi_lo",  # or "lo_hi"
):
    """
    Adds one site (name==uid by default) and 2 cells per sector:
      - sector 0/1/2 @ fc_hi_hz (band_hi) with tilt_hi_deg and antenna config _hi
      - sector 0/1/2 @ fc_lo_hz (band_lo) with tilt_lo_deg and antenna config _lo
    
    Each band (hi/lo) can have its own antenna configuration:
      - bs_rows_hi/lo, bs_cols_hi/lo: Array geometry
      - bs_pol_hi/lo, bs_pol_type_hi/lo: Polarization
      - elem_v_spacing_hi/lo, elem_h_spacing_hi/lo: Element spacing (wavelengths)
      - antenna_pattern_hi/lo: Antenna pattern model
    
    If antenna params are None, uses sim's arr_cfg defaults.
    
    Returns: (site_idx, list_of_cell_indices_in_creation_order)
    """
    # create the site (name & uid uniqueness enforced by your class)
    site_idx = sim.add_site(x, y, height_m=height_m, az0_deg=az0_deg,
                            name=site_name, uid=(uid or site_name))

    added_cells = []
    secs = (0, 1, 2)

    if order not in ("hi_lo", "lo_hi"):
        raise ValueError("order must be 'hi_lo' or 'lo_hi'")

    for sec in secs:
        if order == "hi_lo":
            c_hi = sim.add_cell(site_name, sec, band=band_hi, fc_hz=fc_hi_hz,
                                tilt_deg=tilt_hi_deg, tx_rs_power_dbm=pwr_hi_dbm,
                                bs_rows=bs_rows_hi, bs_cols=bs_cols_hi, 
                                bs_pol=bs_pol_hi, bs_pol_type=bs_pol_type_hi,
                                elem_v_spacing=elem_v_spacing_hi, elem_h_spacing=elem_h_spacing_hi,
                                antenna_pattern=antenna_pattern_hi)
            c_lo = sim.add_cell(site_name, sec, band=band_lo, fc_hz=fc_lo_hz,
                                tilt_deg=tilt_lo_deg, tx_rs_power_dbm=pwr_lo_dbm,
                                bs_rows=bs_rows_lo, bs_cols=bs_cols_lo,
                                bs_pol=bs_pol_lo, bs_pol_type=bs_pol_type_lo,
                                elem_v_spacing=elem_v_spacing_lo, elem_h_spacing=elem_h_spacing_lo,
                                antenna_pattern=antenna_pattern_lo)
            added_cells.extend([c_hi, c_lo])
        else:  # "lo_hi"
            c_lo = sim.add_cell(site_name, sec, band=band_lo, fc_hz=fc_lo_hz,
                                tilt_deg=tilt_lo_deg, tx_rs_power_dbm=pwr_lo_dbm,
                                bs_rows=bs_rows_lo, bs_cols=bs_cols_lo,
                                bs_pol=bs_pol_lo, bs_pol_type=bs_pol_type_lo,
                                elem_v_spacing=elem_v_spacing_lo, elem_h_spacing=elem_h_spacing_lo,
                                antenna_pattern=antenna_pattern_lo)
            c_hi = sim.add_cell(site_name, sec, band=band_hi, fc_hz=fc_hi_hz,
                                tilt_deg=tilt_hi_deg, tx_rs_power_dbm=pwr_hi_dbm,
                                bs_rows=bs_rows_hi, bs_cols=bs_cols_hi,
                                bs_pol=bs_pol_hi, bs_pol_type=bs_pol_type_hi,
                                elem_v_spacing=elem_v_spacing_hi, elem_h_spacing=elem_h_spacing_hi,
                                antenna_pattern=antenna_pattern_hi)
            added_cells.extend([c_lo, c_hi])

    return site_idx, added_cells

def _labels_from_meta(cells_meta, mode="bxy", suffix_freq_on_dup=True):
    labels = []
    seen = {}
    for m in cells_meta:
        if mode == "name":
            base = str(m["name"])
        else:
            base = f"b{int(m['site_id'])+1}{int(m['sector_id'])+1}"
        lab = base
        if base in seen and suffix_freq_on_dup:
            mhz = int(round(float(m["fc_hz"]) / 1e6))
            lab = f"{base}_{mhz}MHz"
        seen[base] = seen.get(base, 0) + 1
        labels.append(lab)
    return labels

def rsrp_rows_as_dicts(RSRP_dBm, cells_meta, *,
                       threshold_dbm=-124.0,
                       user_prefix="user_", user_pad=6,
                       label_mode="bxy",  # or "name"
                       suffix_freq_on_dup=True,
                       ue_locations=None):
    R = np.asarray(RSRP_dBm)
    assert R.ndim == 2, "RSRP_dBm must be [U, C]"
    assert R.shape[1] == len(cells_meta), "C mismatch: columns vs cells_meta"

    labels = _labels_from_meta(cells_meta, mode=label_mode, suffix_freq_on_dup=suffix_freq_on_dup)
    mask = R >= float(threshold_dbm)

    out = []
    for u in range(R.shape[0]):
        row = {"user_id": f"{user_prefix}{u:0{user_pad}d}"}
        
        # Add UE x, y coordinates if provided
        if ue_locations is not None:
            row["x"] = float(ue_locations[u, 0])
            row["y"] = float(ue_locations[u, 1])
        
        for i in np.nonzero(mask[u])[0]:
            row[labels[i]] = float(R[u, i])
        out.append(row)
    return out 

def iter_clustered_sites(n_sites, spacing=600.0, center=(0.0, 0.0), jitter=0.05, seed=42):
    """
    Yield (x, y, az0_deg) for n_sites arranged in a compact cluster (disk).
    - spacing: target inter-site spacing in meters
    - center: (cx, cy) for the cluster center
    - jitter: fraction of spacing for small random perturbation (0 = no jitter)
    """
    random.seed(seed)

    # Golden angle for nice uniform radial fill
    golden_angle = math.radians(137.50776405003785)

    # Choose scale so radius ~ spacing * sqrt(n/pi), keeping density about right
    scale = spacing / math.sqrt(math.pi)

    cx, cy = center
    for i in range(1, n_sites + 1):
        r = scale * math.sqrt(i)
        theta = i * golden_angle

        # Base coordinates in a disk cluster
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)

        # Small jitter to avoid perfect symmetry
        if jitter > 0:
            x += (random.uniform(-1, 1)) * spacing * jitter
            y += (random.uniform(-1, 1)) * spacing * jitter

        # Sector-0 azimuth (rounded to whole degrees, outward from center)
        az0_deg = int(round((math.degrees(theta) + 180.0) % 360.0))

        yield x, y, az0_deg    



