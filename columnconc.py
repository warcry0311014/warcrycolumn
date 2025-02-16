import pandas as pd
import numpy as np
from scipy.optimize import fsolve
from .genconcrete import calc_effdepth, calc_steelarea, calc_betaone, calc_fs, calc_phi_value, get_secproperties, get_matproperties


ALPHA1:float = 0.85
"""
Coefficient for Whitney rectangular stress distribution on concrete. 

Refers to 0.85 in 0.85fc.

"""


def max_nomaxial(b:int, h:int, As:float, fc:int, fy:int) -> float:
    """
    Calculates maximum nominal axial capacity of concrete column with ties per ACI 318-19.

    Args:
        `b` (int): Smaller cross-sectional dimension of concrete section (mm).
        `h` (int): Larger cross-sectional dimension of concrete section (mm).
        `As` (float): Total steel area of concrete section (mm2).
        `fc` (int): Compressive strength of concrete (MPa).
        `fy` (int): Yield strength of steel reinforcement (MPa).
    
    Returns:
        `Pn` (float): Maximum nominal axial compressive strength of concrete column with ties 
        equal to `0.8Po` where `Po` is the axial capacity per ACI 318-19 22.4.2.2 (kN).

    """

    # Gross cross-sectional area
    Ag = b * h      

    component_concrete = (ALPHA1 * fc * Ag)
    component_steel = ((fy - ALPHA1 * fc) * As)
    Po = (component_concrete + component_steel) / 1000
    return 0.8 * Po


# Helper functions for column interaction diagram

def get_fconcrete(c:int, b:int, fc:int) -> float:
    """Calculates force component of concrete area."""

    beta1 = calc_betaone(fc)
    force_concrete = ALPHA1 * fc * beta1 * c * b
    return force_concrete / 1000


def get_fsteel(c:int, d:int, As:float, fc:int, fs:int=None) -> float:
    """Calculates force component of steel area."""

    if fs is not None:
        force_steel = (fs - ALPHA1 * fc) * As
    else:
        force_steel = ((600 * ((c - d) / c) - (ALPHA1 * fc)) * As)
    return force_steel / 1000


def c_solver(c_initial:float, b:int, h:int, dt:int, dc:int, As1:float, As2:float, As:float, fc:int, fy:int, condition:int) -> float:
    """Iteration solver for the value of c on specific condition - Condition 2, Condition 3, and Condition 7."""

    # Case 1
    def iterate_c_waxial(c, b, h, dt, dc, As1, As2, As, fc, fy) -> float:
        """
        Case when concrete is in pure compression. 
        
        Iterate the value of `c` such that the total axial force does not exceed 
        the maximum nominal axial compressive strength, Pn with no bending.

        """
        total_axial = max_nomaxial(b=b, h=h, As=As, fc=fc, fy=fy)
        force_concrete = get_fconcrete(c=c, b=b, fc=fc)
        force_steel1 = get_fsteel(c=c, d=dt, As=As1, fc=fc)
        force_steel2 = get_fsteel(c=c, d=dc, As=As2, fc=fc)
        return force_concrete + force_steel1 + force_steel2 - total_axial
    

    # Case 2
    def iterate_c_steel1(c, d, As1, fc) -> float:
        """
        Case when neutral axis is near tensile steel area.

        Iterate the value of `c` such that the force in tensile steel area is zero
        considering the concrete section already experienced tensile strains on the
        side of the tensile steel area.
        
        """

        # Account the effect of tensile strains in concrete section
        # Deduce 0.85fc from the stress in steel
        force_steel = ((600 * ((c - d) / c) - (ALPHA1 * fc)) * As1)
        return force_steel


    # Case 3
    def iterate_c_woaxial(c, b, dt, dc, As1, As2, fc, fy) -> float:
        """
        Case when concrete is in pure bending. 

        Iterate the value of `c` such that the actual total axial force is zero.
        
        """

        force_concrete = get_fconcrete(c=c, b=b, fc=fc)
        # Since tension steel area is guaranteed to yield, set fs equal to fy
        force_steel1 = get_fsteel(c=c, d=dt, As=As1, fc=fc, fs=-fy)
        force_steel2 = get_fsteel(c=c, d=dc, As=As2, fc=fc)
        return force_concrete + force_steel2 + force_steel1
    

    match condition:
        case 1:
            c_final = fsolve(iterate_c_waxial, c_initial, args=(b, h, dt, dc, As1, As2, As, fc, fy)).item()
        case 2:
            c_final = fsolve(iterate_c_steel1, c_initial, args=(dt, As1, fc)).item()
        case 3:
            c_final = fsolve(iterate_c_woaxial, c_initial, args=(b, dt, dc, As1, As2, fc, fy)).item()

    return c_final


def get_c(b:int, h:int, dt:int, dc:int, As1:float, As2:float, As:float, fc:int, fy:int, condition:int, c_initial:int=None):
    """
    Returns a value of the location of neutral axis, `c` 
    measured from the concrete edge in compression for the following condition:

    1. Condition 2 - Moment capacity at maximum axial compression.
    2. Condition 3 - Zero strain at tensile steel area (on the verge of tension).
    3. Condition 4 - Stress at tensile steel area equal to half of yield strength (0.5fy).
    4. Condition 5 - Balanced condition (concrete fails as tensile steel yields).
    5. Condition 6 - Tensile-controlled condition.
    6. Condition 7 - Pure-bending.

    """

    ESTEEL = 200000
    concstrain = 0.003
    ystrain = fy / ESTEEL
    tcstrain = ystrain + concstrain

    match condition:
        case 2:
            if c_initial is not None:
                return c_solver(c_initial=c_initial, b=b, h=h, dt=dt, dc=dc, As1=As1, As2=As2, As=As, fc=fc, fy=fy, condition=1)
            return c_solver(c_initial=h, b=b, h=h, dt=dt, dc=dc, As1=As1, As2=As2, As=As, fc=fc, fy=fy, condition=1)
        case 3:
            if c_initial is not None:
                return c_solver(c_initial=c_initial, b=b, h=h, dt=dt, dc=dc, As1=As1, As2=As2, As=As, fc=fc, fy=fy, condition=2)
            return c_solver(c_initial=dt, b=b, h=h, dt=dt, dc=dc, As1=As1, As2=As2, As=As, fc=fc, fy=fy, condition=2)
        case 4:
            return dt * (concstrain / (ystrain / 2 + concstrain))
        case 5:
            return dt * (concstrain / (ystrain + concstrain))
        case 6:
            return dt * (concstrain / (tcstrain + concstrain))
        case 7: 
            if c_initial is not None:
                return c_solver(c_initial=c_initial, b=b, h=h, dt=dt, dc=dc, As1=As1, As2=As2, As=As, fc=fc, fy=fy, condition=3)
            return c_solver(c_initial=dc, b=b, h=h, dt=dt, dc=dc, As1=As1, As2=As2, As=As, fc=fc, fy=fy, condition=3)


# Main function for column interaction diagram

def get_cid_coordinate(b:int, h:int, ccover:int, d_main:int, d_trans:int, n_bar:int, n_bar_total:int, fc:int, fy:int, point:int, c_initial:float=None) -> float:
    """
    Determines a pair of phi_Pn and phi_Mn values for plotting the interaction diagram.

    Args:
        `b` (int): Smaller cross-sectional dimension of concrete section (mm).
        `h` (int): Larger cross-sectional dimension of concrete section (mm).
        `ccover` (int): Clear cover of concrete section (mm).
        `d_main`: Size of main reinforcement (mm).
        `d_trans`: Size of transverse reinforcement (i.e. stirrup/ties/spiral) (mm).
        `n_bar`: Number of main bars along a side (i.e. along b or h).
        `n_bar_total`: Total number of main bars in the concrete section.
        `fc` (int): Compressive strength of concrete (MPa).
        `fy` (int): Yield strength of steel reinforcement (MPa).
        `Point` (int): Coordinate to find for the interaction diagram. Must be 1 to 8.
        `c_initial` (float): Initial value of c for `get_c()`. Default is `None`.

    Returns:
        A tuple of phi_Pn and phi_Mn values treated as a coordinate in the plot of interaction diagram
        where phi_Mn is the value along the horizontal axis and phi_Pn is the value along the vertical axis.

    """

    # Cross sectional parameters
    dt, dc = calc_effdepth(h=h, ccover=ccover, d_main=d_main, d_trans=d_trans)
    As1 = calc_steelarea(d_main=d_main, n_bar=n_bar)
    As2 = calc_steelarea(d_main=d_main, n_bar=n_bar)
    As_total = calc_steelarea(d_main=d_main, n_bar=n_bar_total)

    if point == 1:
        PHI = 0.65

        nom_axial, nom_moment = max_nomaxial(b=b, h=h, As=As_total, fc=fc, fy=fy), 0
        return nom_axial * PHI, nom_moment * PHI

    elif point == 8:
        PHI = 0.9

        nom_axial, nom_moment = -(fy * As_total) / 1000, 0
        return nom_axial * PHI, nom_moment * PHI

    else:
        beta1 = calc_betaone(fc=fc)
        c = get_c(b=b, h=h, dt=dt, dc=dc, As1=As1, As2=As2, As=As_total, fc=fc, fy=fy, condition=point, c_initial=c_initial)
        a = beta1 * c

        # Get reduction factor
        if c > dt:
            tsteel_strain = 0.003 * ((c - dt) / c)
        else:
            tsteel_strain = 0.003 * ((dt - c) / c)
        phi_value = calc_phi_value(tstrain=tsteel_strain, fy=fy)


        # Get axial forces
        def get_axial() -> tuple:
            """Calculates actual axial force."""

            fs_steel1, fs_steel2 = calc_fs(c=c, d=dt, fy=fy), calc_fs(c=c, d=dc, fy=fy)
            fsteel1 = get_fsteel(c=c, d=dt, As=As1, fc=fc, fs=fs_steel1)
            fsteel2 = get_fsteel(c=c, d=dc, As=As2, fc=fc, fs=fs_steel2)
            fconcrete = get_fconcrete(c=c, b=b, fc=fc)
            actual_axial = fconcrete + fsteel1 + fsteel2
            return fconcrete, fsteel1, fsteel2, actual_axial


        # Get moment arm for moment of forces
        def get_moment_arm() -> tuple:
            """Calculates moment of axial forces about tension steel area."""

            marm_concrete = dt - a / 2
            marm_steel1 = 0
            marm_steel2 = dt - dc
            marm_axial = -(dt - h / 2)
            return marm_concrete / 1000, marm_steel1 / 1000, marm_steel2 / 1000, marm_axial / 1000


        # Get axial and moment values
        def get_axial_moment_pair() -> tuple:
            """Calculates actual axial force and moment pair."""

            axial_components = get_axial()
            marm_components = get_moment_arm()
            m_components = tuple(p * r for p, r in zip(axial_components, marm_components))

            actual_axial, actual_moment = axial_components[-1], sum(m_components)

            if point == 7:
                # Expected value of axial load at point 6 is close to zero
                # Round off value to simplify it into zero
                actual_axial = round(actual_axial)

            return actual_axial, actual_moment


        nom_axial, nom_moment = get_axial_moment_pair()
        return nom_axial * phi_value, nom_moment * phi_value
    

def check_col_adequacy(input_Pu:float, input_Mu:float, cid_df, col_x:str="phi_Pn", col_y:str="phi_Mn") -> dict:
    """
    Evaluate load demands if they does not exceed calculated capacities based on the interaction diagram.

    Args:
        `input_Pu` (float): Factored axial load (kN).
        `input_Mu` (float): Factored moment (kN-m). 
        `cid_df`: Pandas Dataframe for interaction diagram.
        `col_x` (str): Dataframe column name for axial capacity values (Default: "phi_Pn").
        `col_y` (str): Dataframe column name for moment capacity values (Default: "phi_Mn").
    
    Returns:
        A dictionary with the following key-value pairs.
        `is_adequate` (bool): `True` if load demand does not exceed calculated capacities, otherwise `False`.
        `status` (str): `OK` means load demands does not exceed calculated capacities, otherwise `NG`.
        `summary` (str): Descriptive summary of the result.

    """

    # Check input values. Pu must at least have a value
    if input_Pu is None:
        raise ValueError("Provide at least Pu value as input.")
    
    # Check adequacy in axial
    min_phi_Pn, max_phi_Pn = cid_df[col_x].min(), cid_df[col_x].max()
    if input_Pu < min_phi_Pn or input_Pu > max_phi_Pn:
        return {"is_adequate": False, "status": "NG", "summary": f"Pu is greater than {col_x}"}
    
    # Check adequacy in moment
    if input_Mu != 0:
        # Consider absolute value in moment
        input_Mu = abs(input_Mu)

        cid_df_asc = cid_df.sort_values(by=col_x).reset_index(drop=True)
        for i in range(cid_df.shape[0]):
            # Interpolate corresponding phi_Mn value based on Pu
            # x1 = value_Pn1, x2 = value_Pn2
            # y1 = value_Mn1, y2 = value_Mn2
            # x = input_Pu, y = corr_phi_Mn

            value_Pn1, value_Pn2 = cid_df_asc.loc[i, col_x], cid_df_asc.loc[i + 1, col_x]
            if value_Pn1 <= input_Pu <= value_Pn2:
                value_Mn1, value_Mn2 = cid_df_asc.loc[i, col_y], cid_df_asc.loc[i + 1, col_y]
                corr_phi_Mn = value_Mn1 - ((value_Pn1 - input_Pu) * (value_Mn1 - value_Mn2)) / (value_Pn1 - value_Pn2)
                break

        if input_Mu > corr_phi_Mn:
            return {"is_adequate": False, "status": "NG", "summary": f"Mu is greater than {col_y}"}
    
    return {"is_adequate": True, "status": "OK", "summary": "Load demand does not exceed capacity"}


def check_detailing(secproperties:dict, d_main:int) -> dict:
    """
    Evaluate section properties to reinforcement detailing requirements.

    Per ACI 318-19, the following requirements shall be satisfied.
    1. Allowed steel ratio in columns must be minimum of 1% and maximum of 8%.
    2. For longitudinal (main) reinforcements in columns, clear spacing between bars
    shall be atleast the greatest of 40mm, 1.5d_main, and (4/3)d_agg.

    It is assumed that the size of aggregates, d_agg is 20mm.

    Args:
        `add_secproperties` (dict): Return value from get_secproperties().
        `d_main` (int): Size of main reinforcement (mm).

    Returns:
        A dictionary with the following key-value pairs.
        `is_rho_adequate` (bool): `True` if computed steel ratio is within minimum and maximum values, otherwise `False`.
        `is_cspace_adequate` (bool): `True` if smallest clear spacing in concrete section is greater than the
        maximum required clear spacing, otherwise `False`.

    """
    
    # Define steel ratio requirements
    MIN_STEEL_RATIO, MAX_STEEL_RATIO = 0.01, 0.08

    # Define clear spacing requirements
    AGG_SIZE = 20
    min_req_clear_spacing = max(40, 1.5 * d_main, round(4/3 * AGG_SIZE))

    # Evaluate if steel ratio and clear spacing satisfies requirements
    check_steel_ratio = True if MIN_STEEL_RATIO <= secproperties["rho"] <= MAX_STEEL_RATIO else False
    check_clear_spacing = True if min(secproperties["cspace_b"], secproperties["cspace_h"]) > min_req_clear_spacing else False

    return {"is_rho_adequate": check_steel_ratio, "is_cspace_adequate": check_clear_spacing}