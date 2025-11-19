
import numpy as np
import tensorflow as tf
import math


def _deg2rad(x): return tf.cast(x, tf.float32) * (math.pi / 180.0)

def _tr38901_element_power(az_rad, el_rad,
                           phi_3dB_deg=65.0, theta_3dB_deg=65.0, A_m_deg=30.0):
    """
    3GPP TR 38.901 single-element co-pol power pattern (normalized).
    az_rad: azimuth (radians) w.r.t. boresight (0 at boresight).
    el_rad: elevation (radians) w.r.t. boresight (0 at boresight).
    Uses the common symmetric formulation:
        A_h(φ) = min(12*(φ/φ_3dB)^2, A_m)
        A_v(θ) = min(12*(θ/θ_3dB)^2, A_m)
        A(θ,φ) = min(A_h + A_v, A_m)
        G_rel  = 10^(-A/10)
    Returns linear power (peak = 1).
    """
    az_deg = tf.abs(az_rad) * (180.0 / math.pi)
    el_deg = tf.abs(el_rad) * (180.0 / math.pi)

    A_h = tf.minimum(12.0 * (az_deg / phi_3dB_deg)**2, A_m_deg)
    A_v = tf.minimum(12.0 * (el_deg / theta_3dB_deg)**2, A_m_deg)
    A = tf.minimum(A_h + A_v, A_m_deg)
    return tf.pow(10.0, -A / 10.0)  # linear power

def db_to_linear(power_dB):
    power_dB = np.asarray(power_dB, dtype=float)
    return 10.0 ** (power_dB / 10.0)         

def panelarray_cuts_tf(pa, cut_el_deg=0.0, cut_az_deg=0.0, weights=None):
    """
    Evaluate H- and V-plane cuts of a sionna PanelArray 'pa' using TF ops.
    - Reads geometry/spacing from 'pa' (no re-entry).
    - Uses 'pa' element pattern callable if available; otherwise uses TR 38.901 formula.

    Returns:
        (az_deg_np, H_dB_np), (el_deg_np, V_dB_np)
    """
    # --- geometry from PanelArray (all in wavelengths already for PanelArray) ---
    Nr = int(getattr(pa, "num_rows_per_panel"))
    Nc = int(getattr(pa, "num_cols_per_panel"))
    dv = tf.cast(getattr(pa, "element_vertical_spacing"), tf.float32)     # wavelengths
    dh = tf.cast(getattr(pa, "element_horizontal_spacing"), tf.float32)   # wavelengths

    r = tf.range(Nr, dtype=tf.float32) - (Nr - 1) / 2.0
    c = tf.range(Nc, dtype=tf.float32) - (Nc - 1) / 2.0
    cc, rr = tf.meshgrid(c, r)           # cc: cols (y), rr: rows (z)
    y = tf.reshape(cc * dh, [-1])        # [N] wavelengths
    z = tf.reshape(rr * dv, [-1])        # [N] wavelengths
    N = Nr * Nc

    # optional complex weights
    if weights is None:
        w = tf.ones([N], dtype=tf.complex64)
    else:
        w = tf.convert_to_tensor(weights)
        w = tf.reshape(w, [N])
        if not w.dtype.is_complex:
            w = tf.cast(w, tf.complex64)

    # try to get a callable pattern from the panel
    ant = None
    for name in ("antenna_pattern", "_antenna_pattern", "element_pattern", "_element_pattern"):
        cand = getattr(pa, name, None)
        if callable(cand):
            ant = cand
            break

    # element power (linear). If no callable, use 38.901 closed form.
    def element_power(az, el):
        if ant is not None:
            ep = ant(az, el)
            # dict / tuple / single tensor handling, pick a co-pol component and convert to power
            if isinstance(ep, dict):
                # prefer co- or V if present
                key = "co" if "co" in ep else ("V" if "V" in ep else next(iter(ep)))
                val = tf.convert_to_tensor(ep[key])
            elif isinstance(ep, (tuple, list)):
                val = tf.convert_to_tensor(ep[0])
            else:
                val = tf.convert_to_tensor(ep)
            return (tf.math.abs(val)**2 if val.dtype.is_complex else tf.cast(val, tf.float32))
        # fallback: TR 38.901 element (normalized)
        return _tr38901_element_power(az, el)

    # direction cosines for boresight +x
    def uy(az, el): return tf.cos(el) * tf.sin(az)
    def uz(az, el): return tf.sin(el)

    def composite_power(az, el):
        # phases: 2π * (y*uy + z*uz); r is in wavelengths → k = 2π
        ph = 2.0 * math.pi * (
            tf.expand_dims(y, 1) * tf.expand_dims(uy(az, el), 0) +
            tf.expand_dims(z, 1) * tf.expand_dims(uz(az, el), 0)
        )  # [N, A]
        af = tf.reduce_sum(w[:, None] * tf.exp(1j * tf.cast(ph, tf.complex64)), axis=0)  # [A]
        pe = element_power(az, el)  # [A]
        return pe * tf.cast(tf.math.abs(af)**2, tf.float32)

    # H-plane (el fixed)
    az_deg = tf.linspace(-180.0, 180.0, 721)
    elH = tf.fill([721], tf.cast(cut_el_deg, tf.float32))
    H_lin = composite_power(_deg2rad(az_deg), _deg2rad(elH))
    H_lin /= tf.reduce_max(H_lin)
    H_dB = 10.0 / math.log(10.0) * tf.math.log(H_lin + 1e-12)

    # V-plane (az fixed)
    el_deg = tf.linspace(-90.0, 90.0, 721)
    azV = tf.fill([721], tf.cast(cut_az_deg, tf.float32))
    V_lin = composite_power(_deg2rad(azV), _deg2rad(el_deg))
    V_lin /= tf.reduce_max(V_lin)
    V_dB = 10.0 / math.log(10.0) * tf.math.log(V_lin + 1e-12)

    return (az_deg.numpy(), H_dB.numpy(), H_lin.numpy()), (el_deg.numpy(), V_dB.numpy(), V_lin.numpy())


