
# =============================== #
#   Multi-Cell / Per-Cell Tilt    #
#   Sionna 1.1.0 (no ray tracing) #
# =============================== #

# Configure GPU and logging
import os
if os.getenv("CUDA_VISIBLE_DEVICES") is None:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Import and configure Sionna first
import sionna
from sionna.phy import config as sionna_config
sionna_config.seed = 42  # Must be set before TF import
sionna_config.precision = 'single'

# Now import and configure TensorFlow
import tensorflow as tf
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.experimental.set_memory_growth(gpus[0], True)
    except RuntimeError as e:
        print(e)
tf.get_logger().setLevel('ERROR')

# Other imports
import numpy as np
import matplotlib.pyplot as plt
import time
import datetime
from sionna.phy.channel.tr38901 import PanelArray, UMa
from sionna.phy.ofdm import ResourceGrid
from sionna.phy.channel import OFDMChannel


def _ypr_from_deg(az_deg, tilt_deg=0.0, roll_deg=0.0):
    yaw   = np.deg2rad(az_deg % 360.0).astype(np.float32)
    pitch = -np.deg2rad(tilt_deg).astype(np.float32)   # electrical downtilt = negative pitch
    roll  = np.deg2rad(roll_deg).astype(np.float32)
    return np.array([yaw, pitch, roll], dtype=np.float32)

def _trisector_azimuths(az0_deg):
    az = (np.array([0.0, 120.0, 240.0]) + az0_deg) % 360.0
    return [float(az[0]), float(az[1]), float(az[2])]



class MultiCellSim:
    """
    Sites -> Sectors (3 per site by default) -> Cells (>=1 per sector).
    NEW: Sector holds **azimuth only**; **tilt is per-cell** (per carrier).
    """

    def __init__(self,
                 fc_default_hz=3.5e9,
                 bs_rows=4, bs_cols=4,
                 bs_pol='dual', bs_pol_type='VH',
                 elem_v_spacing=0.5, elem_h_spacing=0.5,  # wavelengths
                 ue_pol='single',
                 fft_size=32, scs_hz=30e3, num_ofdm_symbols=1):
        self.fc_default_hz = float(fc_default_hz)
        self.arr_cfg = dict(
            bs_rows=int(bs_rows), bs_cols=int(bs_cols),
            bs_pol=bs_pol, bs_pol_type=bs_pol_type,
            elem_v_spacing=float(elem_v_spacing),
            elem_h_spacing=float(elem_h_spacing),
            ue_pol=ue_pol,
        )
        self.rg_cfg = dict(fft_size=int(fft_size), scs_hz=float(scs_hz), num_sym=int(num_ofdm_symbols))

        # Sites keep x,y,height and **sector azimuths only**
        self.sites = []   # [{x,y,height, az_deg:[az0,az1,az2]}]
        # Cells live on sectors and carry tilt/roll/height/freq/power
        self.cells = []   # [{site_id, sector_id, fc_hz, tx_rs_power_dbm, tilt_deg, roll_deg, height_m, name}]

        # UEs
        self.ue_loc = None; self.ue_orient = None; self.ue_vel = None; self.in_state = None

        # Results
        self.cells_index = []
        self.RSRP_dBm = None      # [U, C]
        self.best_cell = None     # [U]
        self.best_sector = None   # [U] (site*3 + sector_id)
        self.naming = dict(use_site='id', sector_mode='1based', pattern='{band}{site}{sector}')

    # ---------- sites & sectors ----------
    def add_site(self, x, y, height_m=25.0, az0_deg=0.0, name=None, uid=None):
        """
        Create a site with 3 sectors.
        Uniqueness rules:
          - 'name' must be unique
          - 'uid' must be unique
          - If only one of (name, uid) is provided, the other defaults to the same value.
        Returns the integer site index.
        """
        # If only one is provided, mirror it to the other
        if name is None and uid is None:
            # If nothing given, create a temp unique label
            idx_preview = len(self.sites)
            name = f"site_{idx_preview}"
            uid  = name
        elif name is None:
            name = str(uid)
        elif uid is None:
            uid = str(name)
    
        name = str(name)
        uid  = str(uid)
    
        # Enforce uniqueness
        if any(s.get('name') == name for s in self.sites):
            raise ValueError(f"Duplicate site name '{name}'. Site names must be unique.")
        if any(str(s.get('id')) == uid for s in self.sites):
            raise ValueError(f"Duplicate site uid '{uid}'. Site uids must be unique.")
    
        idx = len(self.sites)
        self.sites.append(dict(
            id=uid,
            name=name,
            x=float(x), y=float(y), height=float(height_m),
            az_deg=_trisector_azimuths(az0_deg)  # [az0, az0+120, az0+240]
        ))
        return idx

    def set_sector_az(self, site, sector_id, az_deg):
        i = self._site_idx(site)
        self.sites[i]['az_deg'][sector_id] = float(az_deg) % 360.0

    def set_site_height(self, site, height_m):
        i = self._site_idx(site)
        self.sites[i]['height'] = float(height_m)




    
    # ---------- cells (per-carrier, per-sector) ----------
    def add_cell(self, site, sector_id, *, band: str, fc_hz,
             tx_rs_power_dbm=0.0, tilt_deg=None, roll_deg=0.0, height_m=None, 
             bs_rows=None, bs_cols=None, bs_pol=None, bs_pol_type=None,
             elem_v_spacing=None, elem_h_spacing=None, antenna_pattern=None,
             name: str|None=None):
        """
        The ONLY way to add a cell.
        - band: your tag used ONLY for naming/reporting (e.g., 'L','M','H' or 'NR', etc.)
        - fc_hz: explicit carrier frequency in Hz (you always set this)
        - name: optional manual override; if omitted, auto-generated from pattern
        - bs_rows, bs_cols, bs_pol, bs_pol_type, elem_v_spacing, elem_h_spacing, antenna_pattern:
          Per-cell antenna config; if None, defaults from __init__ are used
        """
        i = self._site_idx(site)                 # accept site idx / uid / name
        if band is None or str(band)=='':
            raise ValueError("band tag is required (e.g., 'M').")
        if fc_hz is None:
            raise ValueError("fc_hz is required (explicit frequency in Hz).")
        auto = self.make_cell_code(i, int(sector_id), band) if name is None else str(name)
        
        # Enforce cell name uniqueness
        if any(c.get('name') == auto for c in self.cells):
            raise ValueError(f"Duplicate cell name '{auto}'. Cell names must be unique. "
                           f"This usually means you're adding the same band to the same sector at the same site.")
    
        # Use per-cell antenna config or fall back to init defaults
        cell = dict(
            site_id=int(i),
            sector_id=int(sector_id),
            band=str(band),
            fc_hz=float(fc_hz),
            tx_rs_power_dbm=float(tx_rs_power_dbm),
            tilt_deg=(None if tilt_deg is None else float(tilt_deg)),
            roll_deg=float(roll_deg),
            height_m=(None if height_m is None else float(height_m)),
            # Antenna config (per-cell, with defaults from arr_cfg)
            bs_rows=int(bs_rows if bs_rows is not None else self.arr_cfg['bs_rows']),
            bs_cols=int(bs_cols if bs_cols is not None else self.arr_cfg['bs_cols']),
            bs_pol=str(bs_pol if bs_pol is not None else self.arr_cfg['bs_pol']),
            bs_pol_type=str(bs_pol_type if bs_pol_type is not None else self.arr_cfg['bs_pol_type']),
            elem_v_spacing=float(elem_v_spacing if elem_v_spacing is not None else self.arr_cfg['elem_v_spacing']),
            elem_h_spacing=float(elem_h_spacing if elem_h_spacing is not None else self.arr_cfg['elem_h_spacing']),
            antenna_pattern=str(antenna_pattern if antenna_pattern is not None else '38.901'),
            name=auto,
        )
        self.cells.append(cell)
        return len(self.cells) - 1

    def update_cell(self, cell_id, *, site=None, sector_id=None, band=None,
                fc_hz=None, tx_rs_power_dbm=None, tilt_deg=None, roll_deg=None,
                height_m=None, bs_rows=None, bs_cols=None, bs_pol=None, bs_pol_type=None,
                elem_v_spacing=None, elem_h_spacing=None, antenna_pattern=None,
                rename: bool=True):
        c = self.cells[cell_id]
        moved = False
        if site is not None:
            c['site_id'] = int(self._site_idx(site)); moved = True
        if sector_id is not None:
            c['sector_id'] = int(sector_id); moved = True
        if band is not None:
            c['band'] = str(band); moved = True
        if fc_hz is not None:
            c['fc_hz'] = float(fc_hz)
        if tx_rs_power_dbm is not None:
            c['tx_rs_power_dbm'] = float(tx_rs_power_dbm)
        if tilt_deg is not None:
            c['tilt_deg'] = float(tilt_deg)
        if roll_deg is not None:
            c['roll_deg'] = float(roll_deg)
        if height_m is not None:
            c['height_m'] = float(height_m)
        # Antenna config updates
        if bs_rows is not None:
            c['bs_rows'] = int(bs_rows)
        if bs_cols is not None:
            c['bs_cols'] = int(bs_cols)
        if bs_pol is not None:
            c['bs_pol'] = str(bs_pol)
        if bs_pol_type is not None:
            c['bs_pol_type'] = str(bs_pol_type)
        if elem_v_spacing is not None:
            c['elem_v_spacing'] = float(elem_v_spacing)
        if elem_h_spacing is not None:
            c['elem_h_spacing'] = float(elem_h_spacing)
        if antenna_pattern is not None:
            c['antenna_pattern'] = str(antenna_pattern)
        if rename and moved:
            new_name = self.make_cell_code(c['site_id'], c['sector_id'], c['band'])
            # Check for name collision before renaming
            if any(i != cell_id and other_c.get('name') == new_name for i, other_c in enumerate(self.cells)):
                raise ValueError(f"Cannot rename cell {cell_id}: name '{new_name}' already exists. Cell names must be unique.")
            c['name'] = new_name

    def rename_site(self, site, *, name=None, uid=None):
        """
        Rename/re-id a site. Enforces uniqueness across all sites.
        'site' can be index, uid, or name.
        """
        i = self._site_idx(site)
        if name is not None:
            name = str(name)
            if any(j != i and s.get('name') == name for j, s in enumerate(self.sites)):
                raise ValueError(f"Duplicate site name '{name}'.")
            self.sites[i]['name'] = name
        if uid is not None:
            uid = str(uid)
            if any(j != i and str(s.get('id')) == uid for j, s in enumerate(self.sites)):
                raise ValueError(f"Duplicate site uid '{uid}'.")
            self.sites[i]['id'] = uid        

    def list_sites(self):
        """Pretty-print sites with index, id, name, position, height, azimuths."""
        for i, s in enumerate(self.sites):
            azs = ", ".join(f"{a:.1f}°" for a in s['az_deg'])
            print(f"[{i}] id={s.get('id')} name={s.get('name')}  "
                  f"xy=({s['x']:.1f},{s['y']:.1f}) h={s['height']:.1f} m  az=[{azs}]")       

    def sites_table(self, as_dataframe: bool = False):
        rows = []
        # count cells per site
        counts = {}
        for c in self.cells:
            counts[c['site_id']] = counts.get(c['site_id'], 0) + 1
        for i, s in enumerate(self.sites):
            rows.append(dict(
                idx=i,
                id=s.get('id'),
                name=s.get('name'),
                x=s['x'], y=s['y'], height_m=s['height'],
                az0_deg=s['az_deg'][0], az1_deg=s['az_deg'][1], az2_deg=s['az_deg'][2],
                n_cells=counts.get(i, 0),
            ))
        if as_dataframe:
            try:
                import pandas as pd
                return pd.DataFrame(rows)
            except Exception:
                pass
        return rows        

    def clear_cells(self):
        self.cells = []

    def list_cells(self):
        for i, c in enumerate(self.cells):
            s = self.sites[c['site_id']]
            print(f"[{i}] {c.get('name')}  band={c.get('band')}  "
                  f"site={s.get('name')} (uid={s.get('id')}, idx={c['site_id']})  "
                  f"sec={c['sector_id']}  fc={c['fc_hz']/1e9:.3f} GHz  "
                  f"P_RS={c['tx_rs_power_dbm']} dBm  tilt={c['tilt_deg']}°  "
                  f"roll={c['roll_deg']}°  height={c['height_m'] if c['height_m'] is not None else s['height']} m  "
                  f"array={c['bs_rows']}x{c['bs_cols']} {c['bs_pol']} {c['antenna_pattern']}")

    # ---------- UEs ----------
    def drop_ues(self, num_ue, layout='disk', center=None, radius_m=500.0, box_pad_m=500.0, height_m=1.5, seed=7):
        """
        Drop UEs in the simulation area. This REPLACES any existing UEs.
        
        Args:
            num_ue: Number of UEs to drop
            layout: 'disk' or 'box' distribution
            center: (x, y) center point, defaults to mean of sites
            radius_m: Radius for disk layout
            box_pad_m: Padding around sites for box layout
            height_m: UE height
            seed: Random seed for reproducibility
        """
        num_ue = int(num_ue)
        rng = np.random.default_rng(seed)
        if center is None and len(self.sites):
            cx = float(np.mean([s['x'] for s in self.sites])); cy = float(np.mean([s['y'] for s in self.sites]))
        else:
            cx, cy = (0.0, 0.0) if center is None else (float(center[0]), float(center[1]))

        if layout == 'disk':
            r = radius_m * np.sqrt(rng.random(num_ue))
            ph = 2*np.pi * rng.random(num_ue)
            xs = cx + r*np.cos(ph); ys = cy + r*np.sin(ph)
            minx, maxx, miny, maxy = None, None, None, None
        else:
            xs_sites = [s['x'] for s in self.sites] or [0.0]
            ys_sites = [s['y'] for s in self.sites] or [0.0]
            minx, maxx = min(xs_sites)-box_pad_m, max(xs_sites)+box_pad_m
            miny, maxy = min(ys_sites)-box_pad_m, max(ys_sites)+box_pad_m
            xs = rng.uniform(minx, maxx, size=num_ue); ys = rng.uniform(miny, maxy, size=num_ue)

        zs = np.full(num_ue, float(height_m), np.float32)
        self.ue_loc = np.stack([xs.astype(np.float32), ys.astype(np.float32), zs], axis=1)[None, ...]
        self.ue_orient = np.tile(np.array([np.pi, 0.0, 0.0], np.float32), (num_ue,1))[None, ...]
        self.ue_vel = np.zeros_like(self.ue_loc)
        self.in_state = np.zeros((1, num_ue), dtype=bool)
        
        # Store drop parameters for querying
        self.ue_drop_params = dict(
            num_ue=num_ue,
            layout=layout,
            center=(cx, cy),
            radius_m=float(radius_m) if layout == 'disk' else None,
            box_pad_m=float(box_pad_m) if layout == 'box' else None,
            box_bounds=(minx, maxx, miny, maxy) if layout == 'box' else None,
            height_m=float(height_m),
            seed=seed
        )
    
    def get_ue_info(self):
        """
        Get information about the current UE drop.
        
        Returns dictionary with:
            - num_ues: Current number of UEs
            - layout: Drop layout type ('disk' or 'box')
            - drop_params: Parameters used for last drop
            - has_results: Whether compute() has been run
        """
        if self.ue_loc is None:
            return {
                "num_ues": 0,
                "layout": None,
                "drop_params": None,
                "has_results": False,
                "message": "No UEs dropped yet. Call drop_ues() first."
            }
        
        num_ues = int(self.ue_loc.shape[1])
        has_results = self.RSRP_dBm is not None
        
        result = {
            "num_ues": num_ues,
            "layout": self.ue_drop_params.get('layout') if hasattr(self, 'ue_drop_params') else None,
            "drop_params": self.ue_drop_params if hasattr(self, 'ue_drop_params') else None,
            "has_results": has_results,
        }
        
        # Add computed results info if available
        if has_results:
            result["results"] = {
                "num_cells_computed": len(self.cells_index),
                "rsrp_shape": list(self.RSRP_dBm.shape) if self.RSRP_dBm is not None else None,
                "num_ues_with_assignment": int(np.sum(self.best_cell is not None)) if self.best_cell is not None else 0,
            }
        
        return result

    # ---------- compute ----------
    @staticmethod
    def _dbm_to_watt(dbm): return 1e-3 * 10.0**(dbm/10.0)
    @staticmethod
    def _watt_to_dbm(w):   return 10.0*np.log10(np.maximum(w, 1e-30)) + 30.0

    def _cells_grouped_by_fc_and_array(self):
        """
        Group cells by BOTH carrier frequency AND antenna configuration.
        Cells must share the same antenna array to be in the same group.
        Returns: {(fc_hz, bs_rows, bs_cols, bs_pol, ...): [(idx, cell), ...]}
        """
        groups = {}
        for idx, cell in enumerate(self.cells):
            key = (
                float(cell['fc_hz']),
                int(cell['bs_rows']),
                int(cell['bs_cols']),
                str(cell['bs_pol']),
                str(cell['bs_pol_type']),
                float(cell['elem_v_spacing']),
                float(cell['elem_h_spacing']),
                str(cell['antenna_pattern']),
            )
            groups.setdefault(key, []).append((idx, cell))
        return groups

    def _build_geom_for_cells(self, grouped_cells):
        """
        Build geometry tensors for a SAME-frequency group of cells.
        - yaw comes from the sector azimuth
        - pitch (tilt) comes from the **cell** (fallback: 0° if None)
        - roll from the cell (fallback 0°)
        - height from cell.height_m if set, else site height
        """
        locs, oris, meta = [], [], []
        for (ci, cell) in grouped_cells:
            s   = self.sites[cell['site_id']]
            sec = cell['sector_id']
            az  = s['az_deg'][sec]                                  # sector azimuth only
            tilt = 0.0 if cell['tilt_deg'] is None else cell['tilt_deg']  # per-cell tilt
            roll = cell['roll_deg']
            h    = s['height'] if cell['height_m'] is None else cell['height_m']
            locs.append([s['x'], s['y'], h])
            oris.append(_ypr_from_deg(az, tilt, roll))
            meta.append(dict(cell_idx=ci, site_id=cell['site_id'], sector_id=sec))
        bs_loc = np.array(locs, np.float32)[None, ...]
        bs_orient = np.array(oris, np.float32)[None, ...]
        return bs_loc, bs_orient, meta

    def compute(self):
        """
        Minimal compute with chunking:
          - groups cells by carrier AND antenna config (first-seen order; no sorting)
          - processes cells in chunks (self.cells_chunk)
          - processes UEs in chunks (self.ue_chunk)
        Returns:
          RSRP_dBm   : [U, C] numpy array
          cells_meta : list[dict] (len C), entry i == column i
        """
        # Reset all random seeds for each compute call
        sionna_config.seed = 42  # Reset Sionna's internal RNG
        np.random.seed(42)      # Reset NumPy RNG
        tf.random.set_seed(42)  # Reset TensorFlow RNG
        
        if self.ue_loc is None:
            raise RuntimeError("Call drop_ues(...) first.")
        if not self.sites:
            raise RuntimeError("Add at least one site.")
        if not self.cells:
            raise RuntimeError("No cells configured. Use add_cell(site, sector_id, band=..., fc_hz=...).")
    
        groups = self._cells_grouped_by_fc_and_array()  # {(fc_hz, bs_rows, ...): [(idx, cell), ...]}
    
        U = self.ue_loc.shape[1]
        C_total = len(self.cells)
        R_full = np.zeros((U, C_total), np.float32)
        index_meta = [None] * C_total
    
        # chunk sizes
        ue_step = int(getattr(self, "ue_chunk", 0) or U)
        # helper to chunk a list
        def _chunks(lst, k):
            if not k: yield lst
            else:
                for i in range(0, len(lst), k):
                    yield lst[i:i+k]
    
        col = 0  # column pointer within this carrier block
        for array_key, cell_list in groups.items():
            # Unpack antenna config from key
            fc, bs_rows, bs_cols, bs_pol, bs_pol_type, elem_v_spacing, elem_h_spacing, antenna_pattern = array_key
            
            # Build arrays ONCE per (frequency + antenna config) group
            bs_array = PanelArray(
                num_rows_per_panel=int(bs_rows),
                num_cols_per_panel=int(bs_cols),
                polarization=str(bs_pol),
                polarization_type=str(bs_pol_type) if str(bs_pol)=='dual' else 'V',
                antenna_pattern=str(antenna_pattern),
                carrier_frequency=float(fc),
                element_vertical_spacing=float(elem_v_spacing),
                element_horizontal_spacing=float(elem_h_spacing),
            )
            ue_array = PanelArray(
                num_rows_per_panel=1, num_cols_per_panel=1,
                polarization=self.arr_cfg['ue_pol'], polarization_type='V',
                antenna_pattern='omni', carrier_frequency=float(fc),
            )
            ch = UMa(carrier_frequency=float(fc), o2i_model='low',
                     ut_array=ue_array, bs_array=bs_array,
                     direction='downlink',
                     enable_pathloss=True, enable_shadow_fading=False)  # Disable shadow fading for determinism
    
            base_col = col  # remember where this carrier's columns start
    
            for sub_cells in _chunks(cell_list, int(getattr(self, "cells_chunk", 0) or 0)):
                # Geometry for these sub-cells
                bs_loc, bs_orient, _ = self._build_geom_for_cells(sub_cells)
                Bf = bs_loc.shape[1]
    
                rg = ResourceGrid(num_ofdm_symbols=self.rg_cfg['num_sym'],
                                  fft_size=self.rg_cfg['fft_size'],
                                  subcarrier_spacing=self.rg_cfg['scs_hz'],
                                  num_tx=Bf, num_streams_per_tx=1)
                ofdm_ch = OFDMChannel(channel_model=ch, resource_grid=rg, return_channel=True)
    
                # Fill column metas (once)
                for j, (_, cell) in enumerate(sub_cells):
                    index_meta[base_col + j] = dict(
                        name=cell['name'],
                        band=cell.get('band'),
                        fc_hz=cell['fc_hz'],
                        tx_rs_power_dbm=cell['tx_rs_power_dbm'],
                        site_id=cell['site_id'],
                        sector_id=cell['sector_id'],
                        tilt_deg=cell['tilt_deg'],
                        roll_deg=cell['roll_deg'],
                        height_m=cell['height_m'],
                    )
    
                # UE chunks
                for u0 in range(0, U, ue_step):
                    u1 = min(U, u0 + ue_step)
                    ch.set_topology(
                        ut_loc=tf.constant(self.ue_loc[:, u0:u1, :]),
                        bs_loc=tf.constant(bs_loc),
                        ut_orientations=tf.constant(self.ue_orient[:, u0:u1, :]),
                        bs_orientations=tf.constant(bs_orient),
                        ut_velocities=tf.constant(self.ue_vel[:, u0:u1, :]),
                        in_state=tf.constant(self.in_state[:, u0:u1]),
                    )
    
                    x = tf.zeros([1, Bf, bs_array.num_ant, rg.num_ofdm_symbols, rg.fft_size], tf.complex64)
                    _, H = ofdm_ch(x)                                   # [1,u_sub,ue_ant,Bf,bs_ant,S,N]
                    H2 = tf.math.square(tf.abs(H))
                    G  = tf.reduce_mean(tf.reduce_sum(H2, axis=[2,4]), axis=[-1,-2])  # [1,u_sub,Bf]
                    G  = tf.squeeze(G, 0).numpy()                                     # [u_sub,Bf]
    
                    # Write this UE-slice into the right columns
                    for j, (_, cell) in enumerate(sub_cells):
                        P_rs_W = self._dbm_to_watt(cell['tx_rs_power_dbm'])
                        RSRP_W = P_rs_W * G[:, j]
                        R_full[u0:u1, base_col + j] = self._watt_to_dbm(RSRP_W)
    
                    # free references ASAP
                    del H, H2, G, x
    
                base_col += Bf
    
            # advance main column pointer by total cells on this carrier
            col = base_col
    
        self.RSRP_dBm = R_full
        self.cells_index = index_meta
        return self.RSRP_dBm, self.cells_index

    # ---------- plots ----------
    def plot_users(self, color='sector', arrow_len=80.0, title=None):
        if self.RSRP_dBm is None: raise RuntimeError("Run compute() first.")
        # One BS marker per sector (use az only)
        bs_points, yaws = [], []
        for sid, s in enumerate(self.sites):
            for sec_az in s['az_deg']:
                bs_points.append([s['x'], s['y']])
                yaws.append(np.deg2rad(sec_az))
        bs_points = np.array(bs_points, np.float32)
        ue_xy = self.ue_loc[0, :, :2]

        if color == 'sector':
            cvals = self.best_sector; cbar_label = 'Serving sector ID (site*3 + sector)'
        elif color == 'best_rsrp':
            bc = self.best_cell; cvals = self.RSRP_dBm[np.arange(len(bc)), bc]; cbar_label = 'Best-cell received power [dBm]'
        else:
            raise ValueError("color must be 'sector' or 'best_rsrp'")

        plt.figure(figsize=(7.5,7))
        sc = plt.scatter(ue_xy[:,0], ue_xy[:,1], c=cvals, s=8, alpha=0.95)
        plt.scatter(bs_points[:,0], bs_points[:,1], marker='^', s=220, edgecolors='k', linewidths=1.0, zorder=3)
        for i, yaw in enumerate(yaws):
            x, y = bs_points[i]
            plt.arrow(x, y, arrow_len*np.cos(yaw), arrow_len*np.sin(yaw),
                      head_width=18.0, length_includes_head=True, zorder=2)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.title(title or (f"UEs colored by {'serving sector' if color=='sector' else 'best-cell RSRP [dBm]'}"))
        cbar = plt.colorbar(sc); cbar.set_label(cbar_label)
        plt.xlabel('x [m]'); plt.ylabel('y [m]')
        plt.grid(True, linestyle=':'); plt.tight_layout(); plt.show()

    def plot_ue_cells(self, ue_idx=0, top_k=None):
        if self.RSRP_dBm is None: raise RuntimeError("Run compute() first.")
        ue_idx = int(ue_idx)
        vals = self.RSRP_dBm[ue_idx].copy()
        order = np.argsort(-vals); 
        if top_k is not None: order = order[:int(top_k)]
        labels = [self.cells_index[i]['name'] for i in order]
        plt.figure(figsize=(max(6, 0.16*len(order)+4), 3.2))
        plt.bar(np.arange(len(order)), vals[order])
        plt.xticks(np.arange(len(order)), labels, rotation=60, ha='right')
        plt.ylabel('Received power [dBm]')
        plt.title(f'UE {ue_idx}: received power by cell')
        plt.tight_layout(); plt.show()

    def _np(self, x):
        try: return x.numpy()
        except AttributeError: return np.asarray(x)
    
    def get_cell(self, cell_id: int):
        """Return a dict of properties for one cell, including site/cell names and antenna config."""
        c = dict(self.cells[cell_id])  # copy
        s = self.sites[c['site_id']]
        return {
            "cell_idx": int(cell_id),
            "cell_name": c.get("name"),
            "band": c.get("band"),
            "site_idx": int(c["site_id"]),
            "site_name": s.get("name"),
            "site_uid": str(s.get("id")),
            "sector_id": int(c["sector_id"]),
            "sector_label": self._sector_label(int(c["sector_id"])),
            "sector_az_deg": float(s["az_deg"][c["sector_id"]]),
            "fc_hz": float(c["fc_hz"]),
            "fc_MHz": float(c["fc_hz"])/1e6,
            "fc_GHz": float(c["fc_hz"])/1e9,
            "tx_rs_power_dbm": float(c["tx_rs_power_dbm"]),
            "tilt_deg": (None if c["tilt_deg"] is None else float(c["tilt_deg"])),
            "roll_deg": float(c["roll_deg"]),
            "height_m_effective": float(c["height_m"] if c["height_m"] is not None else s["height"]),
            # Antenna configuration
            "bs_rows": int(c["bs_rows"]),
            "bs_cols": int(c["bs_cols"]),
            "bs_pol": str(c["bs_pol"]),
            "bs_pol_type": str(c["bs_pol_type"]),
            "elem_v_spacing": float(c["elem_v_spacing"]),
            "elem_h_spacing": float(c["elem_h_spacing"]),
            "antenna_pattern": str(c["antenna_pattern"]),
        }
    
    def cells_table(self, where: dict | None = None, as_dataframe: bool = False):
        """
        Returns a per-cell table keyed by NAMES (not numeric site_id).
        Columns:
          cell_idx (int, 0-based), cell_name (str), band (str|None),
          site_name (str), site_uid (str), site_idx (int),
          x (float), y (float),
          sector_id (0,1,2), sector_label ('1','2','3' or 'A','B','C'),
          sector_az_deg (float),
          fc_hz (float), fc_MHz (float), fc_GHz (float),
          tx_rs_power_dbm (float), tilt_deg (float|None), roll_deg (float),
          height_m_effective (float),
          bs_rows (int), bs_cols (int), bs_pol (str), bs_pol_type (str),
          elem_v_spacing (float), elem_h_spacing (float), antenna_pattern (str)
    
        Filtering (optional): pass a dict where keys are any column name above (or
        'fc_mhz' / 'fc_ghz' aliases) and values are equality, (min,max) ranges, or callables.
        """
        rows = []
        for i, c in enumerate(self.cells):
            s = self.sites[c['site_id']]
            rows.append(dict(
                cell_idx=i,
                cell_name=c.get('name'),
                band=c.get('band'),
                site_name=s.get('name'),
                site_uid=str(s.get('id')),
                site_idx=int(c['site_id']),
                x=float(s['x']),
                y=float(s['y']),
                sector_id=int(c['sector_id']),
                sector_label=self._sector_label(int(c['sector_id'])),
                sector_az_deg=float(s['az_deg'][c['sector_id']]),
                fc_hz=float(c['fc_hz']),
                fc_MHz=float(c['fc_hz'])/1e6,
                fc_GHz=float(c['fc_hz'])/1e9,
                tx_rs_power_dbm=float(c['tx_rs_power_dbm']),
                tilt_deg=(None if c['tilt_deg'] is None else float(c['tilt_deg'])),
                roll_deg=float(c['roll_deg']),
                height_m_effective=float(c['height_m'] if c['height_m'] is not None else s['height']),
                # Antenna configuration
                bs_rows=int(c['bs_rows']),
                bs_cols=int(c['bs_cols']),
                bs_pol=str(c['bs_pol']),
                bs_pol_type=str(c['bs_pol_type']),
                elem_v_spacing=float(c['elem_v_spacing']),
                elem_h_spacing=float(c['elem_h_spacing']),
                antenna_pattern=str(c['antenna_pattern']),
            ))
    
        # --- filtering ---
        if where:
            def match(row):
                for k, v in where.items():
                    key = k
                    if k.lower() in ('fc_mhz',): key = 'fc_MHz'
                    if k.lower() in ('fc_ghz',): key = 'fc_GHz'
                    rv = row.get(key, None)
                    if callable(v):
                        if not v(rv): return False
                    elif isinstance(v, (tuple, list)) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
                        lo, hi = v
                        if rv is None or not (lo <= rv <= hi): return False
                    else:
                        if rv != v: return False
                return True
            rows = [r for r in rows if match(r)]
    
        if as_dataframe:
            try:
                import pandas as pd
                return pd.DataFrame(rows)
            except Exception:
                pass
        return rows
    
    def summary_by_sector(self, as_dataframe: bool = False):
        """
        Aggregate per-sector view: azimuth, #cells, bands present, tilt stats.
        """
        rows = []
        for sid, s in enumerate(self.sites):
            for sec_id, az in enumerate(s['az_deg']):
                # cells that map to this sector
                c_this = [c for c in self.cells if c['site_id'] == sid and c['sector_id'] == sec_id]
                if not c_this:
                    rows.append(dict(site_id=sid, sector_id=sec_id, az_deg=float(az),
                                     n_cells=0, bands_mhz=[], tilts_specified=0,
                                     tilt_min=None, tilt_max=None))
                    continue
                tilts = [c['tilt_deg'] for c in c_this if c['tilt_deg'] is not None]
                freqs = [int(round(c['fc_hz']/1e6)) for c in c_this]
                rows.append(dict(
                    site_id=sid,
                    sector_id=sec_id,
                    az_deg=float(az),
                    n_cells=len(c_this),
                    bands_mhz=sorted(sorted(set(freqs))),
                    tilts_specified=len(tilts),
                    tilt_min=(float(np.min(tilts)) if tilts else None),
                    tilt_max=(float(np.max(tilts)) if tilts else None),
                ))
        if as_dataframe:
            try:
                import pandas as pd
                return pd.DataFrame(rows)
            except Exception:
                pass
        return rows
    
    def export_cells_csv(self, path: str):
        keys = ["cell_idx","cell_name","band","site_name","site_uid","site_idx",
                "sector_id","sector_label","sector_az_deg",
                "fc_hz","fc_MHz","fc_GHz",
                "tx_rs_power_dbm","tilt_deg","roll_deg","height_m_effective",
                "bs_rows","bs_cols","bs_pol","bs_pol_type",
                "elem_v_spacing","elem_h_spacing","antenna_pattern"]
        rows = self.cells_table(as_dataframe=False)
        try:
            import pandas as pd
            import pathlib
            df = self.cells_table(as_dataframe=True)
            df.to_csv(path, index=False)
        except Exception:
            import csv, pathlib
            pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                for r in rows:
                    w.writerow({k: r.get(k) for k in keys})

    def _site_idx(self, site):
        """Accepts int index, site uid, or site name; returns int index."""
        if isinstance(site, int):
            if 0 <= site < len(self.sites):
                return site
            raise KeyError(f"Site index {site} out of range.")
        key = str(site)
        for i, s in enumerate(self.sites):
            if str(s.get('id')) == key or s.get('name') == key:
                return i
        raise KeyError(f"Unknown site '{site}'. Use an index, existing uid, or name.")

    # ---- helpers (add as methods) ----
    def configure_naming(self, *, use_site='id', sector_mode='1based', pattern=None):
        """use_site: 'id' or 'name'; sector_mode: '1based' or 'ABC'."""
        self.naming['use_site'] = use_site
        self.naming['sector_mode'] = sector_mode
        if pattern is not None:
            self.naming['pattern'] = str(pattern)
    
    def _site_key(self, site_idx: int) -> str:
        s = self.sites[site_idx]
        return str(s['id']) if self.naming['use_site'] == 'id' else str(s['name'])
    
    def _sector_label(self, sector_id: int) -> str:
        return 'ABC'[sector_id] if self.naming['sector_mode']=='ABC' else str(sector_id+1)
    
    def make_cell_code(self, site_idx: int, sector_id: int, band: str|None) -> str:
        band = '' if band is None else str(band)
        site = self._site_key(site_idx)
        sector = self._sector_label(sector_id)
        return self.naming['pattern'].format(band=band, site=site, sector=sector, sector_id=sector_id)    

    def get_metadata(self, *,
                     timestep=None,
                     timestep_minutes=None,   # client can pass what they’re polling with; we just echo
                     include_time: bool = False,   # default: no timestamps
                     auto_increment: bool = True):
        """
        Returns core sim metadata. No timestamps unless include_time=True.

        {
          "timestep": <int>,
          "num_users": <int>,
          "num_bands": <int>,
          "bands": [ ... ],
          "timestep_minutes": <int|None>,
          # optionally (if include_time=True):
          "timestamp": "YYYY-MM-DD_HH-MM-SS",
          "unix_timestamp": <float>
        }
        """
        # UE count
        U = int(self.ue_loc.shape[1]) if (self.ue_loc is not None) else 0

        # Unique bands in first-seen order; fallback to MHz label if band missing
        seen = {}
        bands = []
        for c in self.cells:
            tag = c.get("band")
            if tag is None or str(tag) == "":
                tag = f"{int(round(float(c['fc_hz'])/1e6))}MHz"
            tag = str(tag)
            if tag not in seen:
                seen[tag] = True
                bands.append(tag)

        # Timestep counter tied to *this call* (i.e., to each pull)
        if timestep is None:
            if not hasattr(self, "_timestep_counter"):
                self._timestep_counter = 0
            ts_val = int(self._timestep_counter)
            if auto_increment:
                self._timestep_counter += 1
        else:
            ts_val = int(timestep)

        out = {
            "timestep": ts_val,
            "num_users": U,
            "num_bands": len(bands),
            "bands": bands,
            "timestep_minutes": (None if timestep_minutes is None else int(timestep_minutes)),
        }

        if include_time:
            now = time.time()
            out["timestamp"] = datetime.datetime.fromtimestamp(now).strftime("%Y-%m-%d_%H-%M-%S")
            out["unix_timestamp"] = float(now)

        return out    