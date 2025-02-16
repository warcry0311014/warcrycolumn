import math


STD_REBAR_SIZES:tuple = (10, 12, 16, 20, 25, 28, 32, 36, 40, 50)
"""
List of standard steel reinforcing bars (mm).

1. 10mm - close to #3 (English) or #10 (Metric)
2. 12mm - close to #4 (English) or #13 (Metric)
3. 16mm - close to #5 (English) or #16 (Metric)
4. 20mm - close to #6 (English) or #19 (Metric)
5. 25mm - close to #8 (English) or #25 (Metric)
6. 28mm - close to #9 (English) or #29 (Metric)
7. 32mm - close to #10 (English) or #32 (Metric)
8. 36mm - close to #11 (English) or #36 (Metric)
9. 40mm
10. 50mm

"""

CONCSTRAIN:float = 0.003
"""Default ultimate strain of concrete equal to 0.003."""

MIN_STEEL_RATIO:float = 0.01
"""Minimum steel ratio for a concrete column per ACI 318-19 requirements equal to 0.01."""

MAX_STEEL_RATIO:float = 0.08
"""Maximum steel ratio for a concrete column per ACI 318-19 requirements equal to 0.08."""

AGG_SIZE:int = 20
"""Typical size of aggregate equal to 20mm."""


def calc_effdepth(h:int, ccover:int, d_main:int, d_trans:int=None) -> tuple:
    """
    Calculates effective depth of concrete section for tension and compression side.

    Args:
        `h` (int): Designated depth of concrete section (mm).
        `ccover` (int) : Clear of concrete section (mm).
        `d_main` (int): Size of main reinforcement (mm).
        `d_trans` (int): Size of transverse reinforcement (i.e. stirrup/ties/spiral) (mm).

    If `d_trans` is `None`, it is assumed ccover accounts for the size of d_trans.

    Returns:
        `dt` (int): Effective depth of concrete section at tension side (mm).
        `dc` (int): Effective depth of concrete section at compression side (mm).

    A tuple with the values of `dt` and `dc`
    
    """

    if d_trans is None:
        dt = h - ccover - d_main / 2 
        dc = ccover + d_main / 2
        return dt, dc
    
    dt = h - ccover - d_trans - d_main / 2 
    dc = ccover + d_trans + d_main / 2
    return dt, dc


def calc_steelarea(d_main:int, n_bar:int=2) -> float:
    """Calculates steel area in the concrete section."""

    if n_bar < 2:
        raise ValueError("Invalid number of rebars. Provide atleast two (2) pieces.")
    if d_main not in STD_REBAR_SIZES:
        raise ValueError("Rebar size is not a standard size.")
    
    steel_area = round(n_bar * (d_main ** 2) * math.pi / 4, 3)
    return steel_area


def calc_betaone(fc:int) -> float:
    """Calculates the value of β1 in the concrete section."""

    BASE_VALUE = 0.85
    MIN_FC, MAX_FC = 17, 55
    MAX_NORMAL_STR = 28

    if fc < MIN_FC:
        raise ValueError("fc must be atleast 17 MPa")
    if fc >= MIN_FC and fc <= MAX_NORMAL_STR:
        return BASE_VALUE
    if fc >= MAX_FC:
        return BASE_VALUE
    
    factor_reduction = 0.05 * (fc - MAX_NORMAL_STR) / 7
    return BASE_VALUE - factor_reduction


def calc_fs(c:int, d:int, fy:int) -> float:
    """Calculates stress in steel reinforcing bars."""

    fs = 600 * ((c - d) / c)
    if abs(fs) > fy and fs > 0:
        return fy
    if abs(fs) > fy and fs < 0:
        return -fy
    return fs


def calc_phi_value(tstrain:float, fy:int) -> float:
    """Calculates the strength reduction factor."""

    ESTEEL = 200000
    concstrain = 0.003
    ystrain = fy / ESTEEL
    tcstrain = ystrain + concstrain

    if tstrain <= ystrain:
        return 0.65
    if tstrain >= tcstrain:
        return 0.9
    transstrain = 0.65 + 0.25 * (tstrain - ystrain) / concstrain
    return transstrain


def get_secproperties(b:int, h:int, ccover:int, d_main:int, d_trans:int, n_bar_b:int, n_bar_h:int, n_bar_total:int) -> dict:
    """
    Returns additional section properties based on input section properties.

    Args:
        `b` (int): Smaller cross-sectional dimension of concrete section (mm).
        `h` (int): Larger cross-sectional dimension of concrete section (mm).
        `ccover` (int): Clear cover of concrete section (mm).
        `d_main` (int): Size of main reinforcement (mm).
        `d_trans` (int): Size of transverse reinforcement (i.e. stirrup/ties/spiral) (mm).
        `n_bar_b` (int): Number of main bars along short side of concrete section.
        `n_bar_h` (int): Number of main bars along long side of concrete section.
        `n_bar_total` (int): Total number of main bars in the concrete section.

    Returns:
        A dictionary with the following key-value pairs.
        `gross_area` (float): Gross area of concrete section (mm2).
        `steel_area` (float): Total steel area of concrete section (mm2).
        `rho` (float): Computed steel ratio (%) equal to the ratio of steel area, As and gross area of section, Ag.
        `cspace_b` (float): Computed clear spacing along short side (mm).
        `cspace_h` (float): Computed clear spacing along short side (mm).
    
    """

    # Calculate gross cross-sectional area and total steel area
    Ag, As = b * h, calc_steelarea(d_main=d_main, n_bar=n_bar_total)

    # Calculate steel ratio
    actual_steel_ratio = As / Ag

    # Calculate clear spacing for each side of the concrete section
    clear_spacing_b = (b - (ccover * 2) - (d_trans * 2) - (d_main * n_bar_b)) / (n_bar_b - 1)
    clear_spacing_h = (h - (ccover * 2) - (d_trans * 2) - (d_main * n_bar_h)) / (n_bar_h - 1)

    return {"gross_area": Ag, "steel_area": As, "rho": actual_steel_ratio, "cspace_b": clear_spacing_b, "cspace_h":clear_spacing_h}


def get_matproperties(fc:int, fy:int) -> dict:
    """
    Returns additional material properties based on input compressive strength of concrete and yield strength of steel.
    
    Args:
        `fc` (int): Compressive strength of concrete (MPa).
        `fy` (int): Yield strength of steel reinforcement (MPa).

    Returns:
        A dictionary with the following key-value pairs.
        `elasticity_concrete` (int): Modulus of elasticity of concrete, Ec (MPa).
        `beta1` (float): β1 coefficient relating depth of equivalent rectangular 
        compressive stress block to depth of neutral axis.
        `e_ult` (float): Ultimate strain in concrete (mm/mm) equal to 0.003.
        `elasticity_steel` (int): Modulus of elasticity of steel, Es (MPa) 
        set constant to 200 GPa / 200,000 MPa.
        `ystrain`: Yield strain of steel (mm/mm) equal to fy / Es.

    """

    # For concrete
    Ec = 4700 * math.sqrt(fc)
    beta1 = calc_betaone(fc)
    e_ult = CONCSTRAIN

    # For steel
    Es = 200000
    ystrain = fy / Es

    return {"elasticity_concrete": Ec, "beta1": beta1, "e_ult": e_ult, "elasticity_steel": Es, "ystrain": ystrain}
