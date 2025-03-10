# calculations/thermal.py

"""
Thermal calculation utilities for the Data Center Cooling Calculator.

This module provides functions for heat transfer calculations, including:
- Heat transfer rate calculations
- Log Mean Temperature Difference (LMTD) method
- Effectiveness-NTU (ε-NTU) method
- Heat exchanger dimensioning and analysis
"""

import math
import logging
from typing import Dict, Any, Tuple, List, Optional, Union

logger = logging.getLogger(__name__)

def heat_transfer_rate(mass_flow: float, specific_heat: float, temp_diff: float) -> float:
    """
    Calculate heat transfer rate using Q = ṁ × cp × ΔT.
    
    Args:
        mass_flow: Mass flow rate in kg/s
        specific_heat: Specific heat capacity in kJ/kg·K
        temp_diff: Temperature difference in K (or °C)
        
    Returns:
        Heat transfer rate in kW
    """
    return mass_flow * specific_heat * temp_diff

def mass_flow_from_heat_rate(heat_rate: float, specific_heat: float, temp_diff: float) -> float:
    """
    Calculate required mass flow rate using Q = ṁ × cp × ΔT.
    
    Args:
        heat_rate: Heat transfer rate in kW
        specific_heat: Specific heat capacity in kJ/kg·K
        temp_diff: Temperature difference in K (or °C)
        
    Returns:
        Mass flow rate in kg/s
    """
    if temp_diff <= 0:
        raise ValueError("Temperature difference must be greater than zero")
        
    return heat_rate / (specific_heat * temp_diff)

def volume_flow_from_mass_flow(mass_flow: float, density: float) -> float:
    """
    Convert mass flow rate to volume flow rate.
    
    Args:
        mass_flow: Mass flow rate in kg/s
        density: Fluid density in kg/m³
        
    Returns:
        Volume flow rate in m³/s
    """
    return mass_flow / density

def log_mean_temp_difference(hot_in: float, hot_out: float, 
                            cold_in: float, cold_out: float,
                            flow_arrangement: str = 'counter') -> float:
    """
    Calculate Log Mean Temperature Difference (LMTD) for heat exchanger calculations.
    
    Args:
        hot_in: Hot fluid inlet temperature in °C
        hot_out: Hot fluid outlet temperature in °C
        cold_in: Cold fluid inlet temperature in °C
        cold_out: Cold fluid outlet temperature in °C
        flow_arrangement: Flow arrangement ('counter', 'parallel', or 'cross')
        
    Returns:
        Log Mean Temperature Difference in K (or °C)
    """
    # Calculate temperature differences
    if flow_arrangement.lower() == 'parallel':
        delta_t1 = hot_in - cold_in
        delta_t2 = hot_out - cold_out
    else:  # counter flow or cross flow
        delta_t1 = hot_in - cold_out
        delta_t2 = hot_out - cold_in
    
    # Check if temperature differences are too close (avoiding division by near-zero)
    if abs(delta_t1 - delta_t2) < 0.001:
        return delta_t1  # Avoid division by zero
    
    # Apply correction factor for cross flow
    f = 1.0
    if flow_arrangement.lower() == 'cross':
        # Simplified correction factor for unmixed cross flow
        # In a real implementation, this would be a more detailed calculation
        r = (hot_in - hot_out) / (cold_out - cold_in)
        ntu = -math.log(1 - r)
        f = 0.9  # Simplified correction factor
    
    # Calculate LMTD
    lmtd = (delta_t1 - delta_t2) / math.log(delta_t1 / delta_t2)
    
    return lmtd * f

def effectiveness_ntu_method(c_min: float, c_max: float, ua: float, 
                            exchanger_type: str = 'crossflow') -> float:
    """
    Calculate heat exchanger effectiveness using ε-NTU method.
    
    Args:
        c_min: Minimum heat capacity rate (ṁ × cp) in kW/K
        c_max: Maximum heat capacity rate (ṁ × cp) in kW/K
        ua: Overall heat transfer coefficient × area (UA) in kW/K
        exchanger_type: Heat exchanger type ('counterflow', 'parallelflow', 'crossflow', etc.)
        
    Returns:
        Heat exchanger effectiveness (0-1)
    """
    # Calculate capacity ratio and NTU
    c_ratio = c_min / c_max if c_max > 0 else float('inf')
    ntu = ua / c_min if c_min > 0 else float('inf')
    
    # Calculate effectiveness based on exchanger type
    if exchanger_type.lower() == 'counterflow':
        if c_ratio < 1:
            numerator = 1 - math.exp(-ntu * (1 - c_ratio))
            denominator = 1 - c_ratio * math.exp(-ntu * (1 - c_ratio))
            effectiveness = numerator / denominator
        else:  # c_ratio = 1
            effectiveness = ntu / (1 + ntu)
            
    elif exchanger_type.lower() == 'parallelflow':
        numerator = 1 - math.exp(-ntu * (1 + c_ratio))
        denominator = 1 + c_ratio
        effectiveness = numerator / denominator
        
    elif exchanger_type.lower() == 'crossflow':
        # Simplified equation for unmixed-unmixed crossflow
        if c_ratio < 1:
            term1 = 1 - math.exp(-ntu**0.78 * c_ratio)
            effectiveness = 1 - math.exp(-term1 / c_ratio)
        else:
            effectiveness = 1 - math.exp(1 - math.exp(-ntu))
            
    elif exchanger_type.lower() == 'shell_and_tube':
        # Shell and tube with one shell pass and even number (>=2) of tube passes
        if c_ratio < 1:
            term1 = math.sqrt(1 + c_ratio**2)
            term2 = math.exp(-ntu * term1)
            numerator = 1 - term2
            denominator = 1 - c_ratio * term2
            effectiveness = 2 * numerator / denominator
        else:
            effectiveness = 2 * (1 + c_ratio + math.sqrt(1 + c_ratio**2) * 
                              (1 + math.exp(-ntu * math.sqrt(1 + c_ratio**2))) /
                              (1 - math.exp(-ntu * math.sqrt(1 + c_ratio**2))))
    else:
        # Default to crossflow if type not recognized
        logger.warning(f"Heat exchanger type '{exchanger_type}' not recognized, using crossflow")
        term1 = 1 - math.exp(-ntu**0.78 * c_ratio)
        effectiveness = 1 - math.exp(-term1 / c_ratio)
        
    # Effectiveness must be between 0 and 1
    return max(0.0, min(1.0, effectiveness))

def heat_transfer_coefficient(reynolds: float, prandtl: float, fluid_type: str, 
                             characteristic_length: float, 
                             thermal_conductivity: float,
                             geometry: str = 'tube') -> float:
    """
    Calculate convective heat transfer coefficient.
    
    Args:
        reynolds: Reynolds number
        prandtl: Prandtl number
        fluid_type: Type of fluid ('water', 'air', etc.)
        characteristic_length: Characteristic length in m
        thermal_conductivity: Thermal conductivity in W/m·K
        geometry: Geometry type ('tube', 'plate', etc.)
        
    Returns:
        Heat transfer coefficient in W/m²·K
    """
    # Calculate Nusselt number based on flow conditions and geometry
    nu = _calculate_nusselt_number(reynolds, prandtl, fluid_type, geometry)
    
    # Calculate heat transfer coefficient
    # h = Nu × k / L
    h = nu * thermal_conductivity / characteristic_length
    
    return h

def _calculate_nusselt_number(reynolds: float, prandtl: float, fluid_type: str, 
                              geometry: str) -> float:
    """
    Calculate Nusselt number for heat transfer calculations.
    
    Args:
        reynolds: Reynolds number
        prandtl: Prandtl number
        fluid_type: Type of fluid ('water', 'air', etc.)
        geometry: Geometry type ('tube', 'plate', etc.)
        
    Returns:
        Nusselt number (dimensionless)
    """
    # Select appropriate correlation based on flow conditions and geometry
    if geometry.lower() == 'tube':
        if reynolds < 2300:  # Laminar flow
            # Constant heat flux
            return 4.36
        elif 2300 <= reynolds < 10000:  # Transition flow
            # Gnielinski correlation
            f = (0.79 * math.log(reynolds) - 1.64) ** (-2)
            numerator = f * (reynolds - 1000) * prandtl
            denominator = 1 + 12.7 * math.sqrt(f) * (prandtl**(2/3) - 1)
            return numerator / denominator if denominator > 0 else 3.66
        else:  # Turbulent flow
            # Dittus-Boelter equation
            if fluid_type.lower() in ['water', 'ethylene_glycol', 'propylene_glycol']:
                # Cooling (fluid being cooled)
                return 0.023 * reynolds**0.8 * prandtl**0.4
            else:
                # Heating (fluid being heated)
                return 0.023 * reynolds**0.8 * prandtl**0.3
    
    elif geometry.lower() == 'plate':
        # Correlation for plate heat exchangers
        return 0.4 * reynolds**0.64 * prandtl**0.4
    
    elif geometry.lower() == 'fin':
        # Simplified correlation for finned surfaces
        return 0.134 * reynolds**0.681 * prandtl**0.33
    
    else:
        # Default to tube correlation if geometry not recognized
        logger.warning(f"Geometry '{geometry}' not recognized, using tube correlation")
        return 0.023 * reynolds**0.8 * prandtl**0.4

def overall_heat_transfer_coefficient(h_hot: float, h_cold: float, 
                                     k_wall: float, wall_thickness: float,
                                     fouling_factor_hot: float = 0.0,
                                     fouling_factor_cold: float = 0.0) -> float:
    """
    Calculate overall heat transfer coefficient (U-value).
    
    Args:
        h_hot: Hot side heat transfer coefficient in W/m²·K
        h_cold: Cold side heat transfer coefficient in W/m²·K
        k_wall: Thermal conductivity of wall material in W/m·K
        wall_thickness: Wall thickness in m
        fouling_factor_hot: Hot side fouling factor in m²·K/W
        fouling_factor_cold: Cold side fouling factor in m²·K/W
        
    Returns:
        Overall heat transfer coefficient in W/m²·K
    """
    # Calculate thermal resistances
    r_hot = 1 / h_hot
    r_wall = wall_thickness / k_wall
    r_cold = 1 / h_cold
    r_fouling = fouling_factor_hot + fouling_factor_cold
    
    # Calculate overall heat transfer coefficient
    # U = 1 / (Rₕₒₜ + Rᵥᵥₐₗₗ + Rᵣₒᵤₗᵢₙₑ + Rₖₒᵢₗ)
    u_value = 1 / (r_hot + r_wall + r_fouling + r_cold)
    
    return u_value

def heat_exchanger_area(heat_load: float, u_value: float, lmtd: float) -> float:
    """
    Calculate required heat exchanger area.
    
    Args:
        heat_load: Heat load in W
        u_value: Overall heat transfer coefficient in W/m²·K
        lmtd: Log Mean Temperature Difference in K
        
    Returns:
        Required heat exchanger area in m²
    """
    # A = Q / (U × LMTD)
    return heat_load / (u_value * lmtd)

def fin_efficiency(h: float, k: float, fin_thickness: float, fin_length: float) -> float:
    """
    Calculate fin efficiency for finned heat exchangers.
    
    Args:
        h: Heat transfer coefficient in W/m²·K
        k: Thermal conductivity of fin material in W/m·K
        fin_thickness: Fin thickness in m
        fin_length: Fin length in m
        
    Returns:
        Fin efficiency (0-1)
    """
    # Calculate fin parameter
    m = math.sqrt(2 * h / (k * fin_thickness))
    
    # Calculate fin efficiency
    # η = tanh(mL) / (mL)
    eta = math.tanh(m * fin_length) / (m * fin_length)
    
    return eta

def fin_effectiveness(fin_efficiency: float, fin_area: float, base_area: float) -> float:
    """
    Calculate fin effectiveness for finned heat exchangers.
    
    Args:
        fin_efficiency: Fin efficiency (0-1)
        fin_area: Fin surface area in m²
        base_area: Base surface area in m²
        
    Returns:
        Fin effectiveness
    """
    # Calculate fin effectiveness
    # ε = 1 + (Aᵢᵢₙ/Aᵦₐₛₑ) × η
    effectiveness = 1 + (fin_area / base_area) * fin_efficiency
    
    return effectiveness

def water_cooling_capacity(flow_rate: float, delta_t: float, 
                          fluid_density: float = 998.0, 
                          fluid_specific_heat: float = 4.182) -> float:
    """
    Calculate water cooling capacity.
    
    Args:
        flow_rate: Water flow rate in m³/h
        delta_t: Temperature difference in K (or °C)
        fluid_density: Fluid density in kg/m³
        fluid_specific_heat: Specific heat capacity in kJ/kg·K
        
    Returns:
        Cooling capacity in kW
    """
    # Convert flow rate from m³/h to kg/s
    mass_flow = flow_rate * fluid_density / 3600
    
    # Calculate cooling capacity
    # Q = ṁ × cₚ × ΔT
    cooling_capacity = mass_flow * fluid_specific_heat * delta_t
    
    return cooling_capacity
