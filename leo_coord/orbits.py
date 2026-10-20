"""Lan truyền quỹ đạo vệ tinh LEO/NGSO.

- Quỹ đạo tròn giải tích (đủ cho chòm sao Walker quy hoạch).
- Nạp TLE qua SGP4 để theo dõi vệ tinh đã phóng (xấp xỉ sàng lọc).

Mô hình Trái Đất cầu bán kính R_EARTH; góc GMST chuẩn.
Mọi thời gian tính bằng giây Unix (t_unix).
"""
from __future__ import annotations

import math
import numpy as np

MU = 398600.4418  # km^3/s^2 — hằng số hấp dẫn Trái Đất
R_EARTH = 6371.0  # km
OMEGA_EARTH = 7.2921159e-5  # rad/s


class CircularOrbit:
    """Một vệ tinh trên quỹ đạo tròn."""

    def __init__(self, alt_km: float, inc_deg: float, raan_deg: float,
                 phase_deg: float, name: str = ""):
        self.alt_km = float(alt_km)
        self.a = R_EARTH + self.alt_km
        self.inc = math.radians(inc_deg)
        self.raan = math.radians(raan_deg)
        self.phase = math.radians(phase_deg)
        self.n = math.sqrt(MU / self.a ** 3)  # rad/s
        self.period_s = 2.0 * math.pi / self.n
        self.name = name

    def eci(self, t) -> np.ndarray:
        """Vị trí ECI (km), shape (..., 3). t: giây (scalar hoặc array)."""
        t = np.asarray(t, dtype=float)
        u = self.phase + self.n * t
        xp = self.a * np.cos(u)
        yp = self.a * np.sin(u)
        ci, si = math.cos(self.inc), math.sin(self.inc)
        cr, sr = math.cos(self.raan), math.sin(self.raan)
        x = xp * cr - yp * ci * sr
        y = xp * sr + yp * ci * cr
        z = yp * si
        return np.stack([x, y, z], axis=-1)


def gmst_rad(t_unix) -> np.ndarray:
    """Góc giờ Greenwich trung bình (radian) tại thời điểm Unix."""
    t_unix = np.asarray(t_unix, dtype=float)
    d = t_unix / 86400.0  # số ngày kể từ 1970-01-01T00:00Z
    days_j2000 = d - 10957.5  # số ngày kể từ J2000 (2000-01-01 12h)
    T = days_j2000 / 36525.0
    g = (280.46061837 + 360.98564736629 * days_j2000
         + 0.000387933 * T ** 2 - T ** 3 / 38710000.0)
    return np.radians(np.mod(g, 360.0))


def eci_to_ecef(pos_eci: np.ndarray, t_unix) -> np.ndarray:
    """Xoay ECI -> ECEF bằng GMST. pos_eci shape (..., 3)."""
    pos = np.asarray(pos_eci, dtype=float)
    g = gmst_rad(t_unix)
    g = np.asarray(g, dtype=float)
    cg, sg = np.cos(g), np.sin(g)
    # phát sóng g cho khớp shape (...,3): g có shape của t
    while cg.ndim < pos.ndim - 1:
        cg = cg[..., None]
        sg = sg[..., None]
    x = pos[..., 0] * cg + pos[..., 1] * sg
    y = -pos[..., 0] * sg + pos[..., 1] * cg
    z = pos[..., 2]
    return np.stack([x, y, z], axis=-1)


def subpoint(ecef: np.ndarray):
    """Điểm chiếu vệ tinh: (lat_deg, lon_deg, alt_km). ecef shape (...,3)."""
    ecef = np.asarray(ecef, dtype=float)
    r = np.linalg.norm(ecef, axis=-1)
    lat = np.degrees(np.arcsin(np.clip(ecef[..., 2] / r, -1.0, 1.0)))
    lon = np.degrees(np.arctan2(ecef[..., 1], ecef[..., 0]))
    return lat, lon, r - R_EARTH


def elevation_and_range(sat_ecef: np.ndarray, gs_lat_deg: float, gs_lon_deg: float):
    """Góc ngẩng (độ) và cự ly (km) từ trạm mặt đất tới vệ tinh.

    sat_ecef: shape (..., 3). Trả về (elevation_deg, range_km) cùng shape (...).
    """
    sat = np.asarray(sat_ecef, dtype=float)
    lat = math.radians(gs_lat_deg)
    lon = math.radians(gs_lon_deg)
    gs = R_EARTH * np.array([math.cos(lat) * math.cos(lon),
                             math.cos(lat) * math.sin(lon),
                             math.sin(lat)])
    up = gs / np.linalg.norm(gs)
    rho = sat - gs
    rng = np.linalg.norm(rho, axis=-1)
    sin_el = np.sum(rho * up, axis=-1) / rng
    el = np.degrees(np.arcsin(np.clip(sin_el, -1.0, 1.0)))
    return el, rng


class WalkerConstellation:
    """Chòm sao Walker (delta: RAAN trải 360°, star: trải 180°)."""

    def __init__(self, name: str, alt_km: float, inc_deg: float,
                 n_sats: int, n_planes: int, phasing: int = 1,
                 kind: str = "delta"):
        if kind not in ("delta", "star"):
            raise ValueError("kind phải là 'delta' hoặc 'star'")
        self.name = name
        self.alt_km = float(alt_km)
        self.inc_deg = float(inc_deg)
        self.n_sats = int(n_sats)
        self.n_planes = int(n_planes)
        self.kind = kind
        a = R_EARTH + self.alt_km
        n = math.sqrt(MU / a ** 3)
        self.period_s = 2.0 * math.pi / n

        base, extra = divmod(self.n_sats, self.n_planes)
        spread = 360.0 if kind == "delta" else 180.0
        ns, phases, raans, incs = [], [], [], []
        for p in range(self.n_planes):
            count = base + (1 if p < extra else 0)
            raan = p * spread / self.n_planes
            for s in range(count):
                phase = (360.0 / count) * s + p * phasing * (360.0 / self.n_sats)
                ns.append(n)
                phases.append(math.radians(phase % 360.0))
                raans.append(math.radians(raan))
                incs.append(math.radians(self.inc_deg))
        self._n = np.array(ns)
        self._phase = np.array(phases)
        self._raan = np.array(raans)
        self._inc = np.array(incs)
        self._a = a
        self.sat_names = [f"{name}-{i:04d}" for i in range(len(ns))]

    @property
    def size(self) -> int:
        return len(self._n)

    def ecef_positions(self, t_unix) -> np.ndarray:
        """Vị trí ECEF mọi vệ tinh, shape (T, S, 3)."""
        t = np.asarray(t_unix, dtype=float).reshape(-1)
        u = self._phase[:, None] + self._n[:, None] * t[None, :]  # (S, T)
        xp = self._a * np.cos(u)
        yp = self._a * np.sin(u)
        ci, si = np.cos(self._inc)[:, None], np.sin(self._inc)[:, None]
        cr, sr = np.cos(self._raan)[:, None], np.sin(self._raan)[:, None]
        x = xp * cr - yp * ci * sr
        y = xp * sr + yp * ci * cr
        z = yp * si
        eci = np.stack([x, y, z], axis=-1)  # (S, T, 3)
        g = gmst_rad(t)  # (T,)
        cg, sg = np.cos(g)[None, :, None], np.sin(g)[None, :, None]
        xe = eci[..., 0] * cg[..., 0] + eci[..., 1] * sg[..., 0]
        ye = -eci[..., 0] * sg[..., 0] + eci[..., 1] * cg[..., 0]
        ze = eci[..., 2]
        ecef = np.stack([xe, ye, ze], axis=-1)  # (S, T, 3)
        return np.transpose(ecef, (1, 0, 2))  # (T, S, 3)


class TLEConstellation:
    """Chòm sao nạp từ TLE (SGP4).

    Tọa độ TEME của SGP4 được xoay về ECEF bằng GMST — xấp xỉ ở mức
    sàng lọc (sai số ~km), đủ cho phân tích phủ sóng/phối hợp sơ bộ.
    """

    def __init__(self, name: str, tles):
        try:
            from sgp4.api import Satrec, jday
        except ImportError as e:
            raise ImportError("Cần gói 'sgp4' để dùng TLEConstellation") from e
        self.name = name
        self._jday = jday
        self.sats = []
        for tle in tles:
            l1, l2 = (tle[1], tle[2]) if len(tle) == 3 else (tle[0], tle[1])
            self.sats.append(Satrec.twoline2rv(l1, l2))
        jd0, _ = jday(1970, 1, 1, 0, 0, 0.0)
        self._jd0 = jd0

    @property
    def size(self) -> int:
        return len(self.sats)

    def ecef_positions(self, t_unix) -> np.ndarray:
        t = np.asarray(t_unix, dtype=float).reshape(-1)
        out = np.zeros((t.size, len(self.sats), 3))
        g = gmst_rad(t)
        cg, sg = np.cos(g), np.sin(g)
        for i, sat in enumerate(self.sats):
            for k, tk in enumerate(t):
                _, r, _ = sat.sgp4(self._jd0 + tk / 86400.0, 0.0)
                x, y, z = r
                out[k, i, 0] = x * cg[k] + y * sg[k]
                out[k, i, 1] = -x * sg[k] + y * cg[k]
                out[k, i, 2] = z
        return out
