import numpy as np
import matplotlib.pyplot as plt




def rel_to_360_angle_convert(angles):
    angles = (angles + 360.0) % 360.0
    return angles

def _hpbw(angles_deg, pattern_dB):
    a = np.asarray(angles_deg); p = np.asarray(pattern_dB)
    i0 = int(np.argmax(p)); peak = p[i0]; tgt = peak - 3.0
    def cross_left():
        for i in range(i0, 0, -1):
            if (p[i-1]-tgt)*(p[i]-tgt) <= 0:
                x1, x2, y1, y2 = a[i-1], a[i], p[i-1], p[i]
                return x1+(tgt-y1)*(x2-x1)/(y2-y1+1e-12)
        return None
    def cross_right():
        for i in range(i0, len(p)-1):
            if (p[i]-tgt)*(p[i+1]-tgt) <= 0:
                x1, x2, y1, y2 = a[i], a[i+1], p[i], p[i+1]
                return x1+(tgt-y1)*(x2-x1)/(y2-y1+1e-12)
        return None
    L, R = cross_left(), cross_right()
    return (R-L if L is not None and R is not None else None), L, R

def _polar_plot(ax, angles_deg, gain_dB, title="", zero_at="E", clockwise=True, floor_dB=-30):
    ang = (np.asarray(angles_deg) % 360.0)
    g = np.asarray(gain_dB)
    r = g - floor_dB
    th = np.deg2rad(ang)
    ax.plot(th, r, color="C0")
    ax.set_title(title, pad=16)
    ax.set_theta_zero_location(zero_at)
    ax.set_theta_direction(-1 if clockwise else 1)
    rings = np.arange(np.ceil(floor_dB/5)*5, 5, 5)
    rings = rings[(rings >= floor_dB) & (rings <= 0)]
    ax.set_rticks([v - floor_dB for v in rings])
    ax.set_yticklabels([f"{int(v)}" for v in rings])
    ax.set_rmin(0); ax.set_rmax(0 - floor_dB + 0.5)
    ax.set_thetagrids(np.arange(0, 360, 45))

def plot_cuts_4up(H_angles, H_dB, V_angles, V_dB, floor_dB=-30, figsize=(11,10)):
    """2×2 grid: polar left, HPBW Cartesian right (red dotted HPBW lines, -3 dB line labeled)."""
    H_dB = np.asarray(H_dB) - np.max(H_dB)
    V_dB = np.asarray(V_dB) - np.max(V_dB)

    H_hpbw, H_L, H_R = _hpbw(H_angles, H_dB)
    V_hpbw, V_L, V_R = _hpbw(V_angles, V_dB)

    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(2, 2)

    # Horizontal polar
    axH_p = fig.add_subplot(gs[0,0], projection="polar")
    _polar_plot(axH_p, H_angles, H_dB, "Horizontal cut  $G(\\pi/2,\\,\\phi)$",
                zero_at="E", clockwise=True, floor_dB=floor_dB)

    # Horizontal Cartesian
    axH_c = fig.add_subplot(gs[0,1])
    axH_c.plot(H_angles, H_dB, color="C0")
    axH_c.set_title("Horizontal cut  $G(\\pi/2,\\,\\phi)$")
    axH_c.set_xlabel("Azimuth (deg)"); axH_c.set_ylabel("Normalized Gain (dB)")
    axH_c.grid(True, linestyle="--", alpha=0.5)
    axH_c.set_ylim(floor_dB, 1); axH_c.set_xlim(min(H_angles), max(H_angles))

    # −3 dB line (gray) + label
    axH_c.axhline(-3, color="red", linestyle=":", linewidth=1)
    axH_c.text(0.98, ( -3 - floor_dB )/(1 - floor_dB), "−3 dB",
               transform=axH_c.transAxes, ha="right", va="bottom",
               color="black", fontsize=9)

    # HPBW lines
    if H_L is not None and H_R is not None:
        for x in (H_L, H_R):
            axH_c.axvline(x, color="red", linestyle=":", linewidth=1.2)
        axH_c.text(0.02, 0.96, f"HPBW ≈ {H_hpbw:.1f}°",
                   transform=axH_c.transAxes, va="top", ha="left",
                   color="red")

    # Vertical polar
    axV_p = fig.add_subplot(gs[1,0], projection="polar")
    _polar_plot(axV_p, V_angles, V_dB, "Vertical cut  $G(\\theta,\\,0)$",
                zero_at="N", clockwise=True, floor_dB=floor_dB)

    # Vertical Cartesian
    axV_c = fig.add_subplot(gs[1,1])
    axV_c.plot(V_angles, V_dB, color="C0")
    axV_c.set_title("Vertical cut  $G(\\theta,\\,0)$")
    axV_c.set_xlabel("Elevation (deg)"); axV_c.set_ylabel("Normalized Gain (dB)")
    axV_c.grid(True, linestyle="--", alpha=0.5)
    axV_c.set_ylim(floor_dB, 1); axV_c.set_xlim(min(V_angles), max(V_angles))
    axV_c.axhline(-3, color="red", linestyle=":", linewidth=1)
    axV_c.text(0.98, ( -3 - floor_dB )/(1 - floor_dB), "−3 dB",
               transform=axV_c.transAxes, ha="right", va="bottom",
               color="black", fontsize=9)

    if V_L is not None and V_R is not None:
        for x in (V_L, V_R):
            axV_c.axvline(x, color="red", linestyle=":", linewidth=1.2)
        axV_c.text(0.02, 0.96, f"HPBW ≈ {V_hpbw:.1f}°",
                   transform=axV_c.transAxes, va="top", ha="left",
                   color="red")

    fig.tight_layout()
    return fig


def _nearest_index_circular(angles_deg, target_deg):
    """
    Return index of the sample in angles_deg closest to target_deg,
    accounting for 360° wrap.
    """
    ang = np.asarray(angles_deg, float)
    # wrap difference into [-180, 180)
    diff = (ang - target_deg + 540.0) % 360.0 - 180.0
    return int(np.argmin(np.abs(diff)))

def roll_beam_cut(angles, vals, target_boresight_deg):
    """
    Roll the horizontal cut values so that the value that was at 0°
    lands at target_boresight_deg on the SAME angle axis.

    H_angles: 1D angles in degrees (any domain, e.g., [-180,180] or [0,360))
    H_vals  : 1D pattern values (dB or linear), same length
    target_boresight_deg: where you want boresight to appear on that axis
    """
    angles = np.asarray(angles, float)
    vals   = np.asarray(vals,   float)

    idx_0   = _nearest_index_circular(angles, 0.0)
    idx_tgt = _nearest_index_circular(angles, target_boresight_deg)

    shift = (idx_tgt - idx_0) % len(vals)
    vals_rot = np.roll(vals, shift)
    return vals_rot    


def save_beamcuts_npz_min(path, H_angles, H_dB, H_lin, V_angles, V_dB, V_lin):
    np.savez_compressed(
        path,
        H_angles=np.asarray(H_angles, dtype=np.float32),
        H_dB=np.asarray(H_dB, dtype=np.float32),
        H_lin=np.asarray(H_lin, dtype=np.float32),
        V_angles=np.asarray(V_angles, dtype=np.float32),
        V_dB=np.asarray(V_dB, dtype=np.float32),
        V_lin=np.asarray(V_lin, dtype=np.float32),
    )    