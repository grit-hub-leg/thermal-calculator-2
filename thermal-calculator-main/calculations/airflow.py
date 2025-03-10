# calculations/airflow.py

"""
Airflow calculation utilities for the Data Center Cooling Calculator.

This module provides functions for air-side calculations, including:
- Fan performance based on fan laws
- Air flow requirements for cooling
- Pressure drop through components
- Fan power consumption and efficiency
- Noise level estimation
"""

import math
import logging
from typing import Dict, Any, Tuple, List, Optional, Union

logger = logging.getLogger(__name__)

# Constants
AIR_DENSITY_SEA_LEVEL = 1.2  # kg/m³ at 20°C
AIR_SPECIFIC_HEAT = 1.005  # kJ/kg·K
STANDARD_PRESSURE = 101325  # Pa (1 atm)

def air_density_at_altitude(altitude: float, temperature: float = 20) -> float:
    """
    Calculate air density at a given altitude and temperature.
    
    Args:
        altitude: Altitude in meters
        temperature: Temperature in °C
        
    Returns:
        Air density in kg/m³
    """
    # Temperature in Kelvin
    temp_k = temperature + 273.15
    
    # Standard atmospheric lapse rate: 0.0065 K/m
    temp_at_altitude = 288.15 - 0.0065 * altitude
    
    # Simplified barometric formula
    pressure_ratio = (temp_at_altitude / 288.15) ** 5.255
    pressure_at_altitude = STANDARD_PRESSURE * pressure_ratio
    
    # Ideal gas law: ρ = P / (R * T)
    # R (specific gas constant for dry air) = 287.058 J/(kg·K)
    density = pressure_at_altitude / (287.058 * temp_k)
    
    return density

def required_air_flow(cooling_kw: float, air_density: float, specific_heat: float, 
                     temp_diff: float) -> float:
    """
    Calculate required air flow for given cooling capacity.
    
    Args:
        cooling_kw: Cooling capacity in kW
        air_density: Air density in kg/m³
        specific_heat: Specific heat capacity of air in kJ/kg·K
        temp_diff: Temperature difference between inlet and outlet in K (or °C)
        
    Returns:
        Required air flow in m³/h
    """
    # Check for invalid inputs
    if cooling_kw <= 0:
        raise ValueError("Cooling capacity must be greater than zero")
    if temp_diff <= 0:
        raise ValueError("Temperature difference must be greater than zero")
    if air_density <= 0:
        raise ValueError("Air density must be greater than zero")
    
    # Convert cooling capacity to W
    cooling_w = cooling_kw * 1000
    
    # Calculate required mass flow rate (kg/s)
    # Q = ṁ × cp × ΔT
    # ṁ = Q / (cp × ΔT)
    mass_flow_rate = cooling_w / (specific_heat * 1000 * temp_diff)
    
    # Convert to volumetric flow rate (m³/h)
    # ṁ = ρ × V̇
    # V̇ = ṁ / ρ
    volumetric_flow_rate = (mass_flow_rate / air_density) * 3600
    
    return volumetric_flow_rate

def fan_laws_flow(flow1: float, speed1: float, speed2: float) -> float:
    """
    Calculate new flow rate based on fan laws (first fan law).
    
    Q₂ = Q₁ × (N₂/N₁)
    
    Args:
        flow1: Original flow rate in m³/h
        speed1: Original fan speed in RPM or %
        speed2: New fan speed in RPM or %
        
    Returns:
        New flow rate in m³/h
    """
    if speed1 <= 0:
        raise ValueError("Original speed must be greater than zero")
    
    return flow1 * (speed2 / speed1)

def fan_laws_pressure(pressure1: float, speed1: float, speed2: float) -> float:
    """
    Calculate new pressure based on fan laws (second fan law).
    
    P₂ = P₁ × (N₂/N₁)²
    
    Args:
        pressure1: Original pressure in Pa
        speed1: Original fan speed in RPM or %
        speed2: New fan speed in RPM or %
        
    Returns:
        New pressure in Pa
    """
    if speed1 <= 0:
        raise ValueError("Original speed must be greater than zero")
    
    return pressure1 * ((speed2 / speed1) ** 2)

def fan_laws_power(power1: float, speed1: float, speed2: float) -> float:
    """
    Calculate new power consumption based on fan laws (third fan law).
    
    W₂ = W₁ × (N₂/N₁)³
    
    Args:
        power1: Original power consumption in W
        speed1: Original fan speed in RPM or %
        speed2: New fan speed in RPM or %
        
    Returns:
        New power consumption in W
    """
    if speed1 <= 0:
        raise ValueError("Original speed must be greater than zero")
    
    return power1 * ((speed2 / speed1) ** 3)

def fan_speed_for_flow(required_flow: float, nominal_flow: float, nominal_speed: float) -> float:
    """
    Calculate required fan speed to achieve a specific flow rate.
    
    N₂ = N₁ × (Q₂/Q₁)
    
    Args:
        required_flow: Required flow rate in m³/h
        nominal_flow: Nominal flow rate in m³/h
        nominal_speed: Nominal fan speed in RPM or %
        
    Returns:
        Required fan speed in RPM or %
    """
    if nominal_flow <= 0:
        raise ValueError("Nominal flow must be greater than zero")
    
    return nominal_speed * (required_flow / nominal_flow)

def fan_speed_for_pressure(required_pressure: float, nominal_pressure: float, 
                          nominal_speed: float) -> float:
    """
    Calculate required fan speed to achieve a specific pressure.
    
    N₂ = N₁ × √(P₂/P₁)
    
    Args:
        required_pressure: Required pressure in Pa
        nominal_pressure: Nominal pressure in Pa
        nominal_speed: Nominal fan speed in RPM or %
        
    Returns:
        Required fan speed in RPM or %
    """
    if nominal_pressure <= 0:
        raise ValueError("Nominal pressure must be greater than zero")
    
    return nominal_speed * math.sqrt(required_pressure / nominal_pressure)

def static_pressure_drop(flow_rate: float, component_type: str, dimensions: Dict[str, float]) -> float:
    """
    Calculate static pressure drop through a component.
    
    Args:
        flow_rate: Flow rate in m³/h
        component_type: Type of component ('filter', 'coil', 'duct', etc.)
        dimensions: Dictionary of component dimensions
        
    Returns:
        Pressure drop in Pa
    """
    # Convert flow rate from m³/h to m³/s
    flow_rate_m3s = flow_rate / 3600
    
    # Calculate pressure drop based on component type
    if component_type.lower() == 'filter':
        # Simplified model: ΔP = k × v²
        # where v is face velocity and k is filter resistance coefficient
        filter_area = dimensions.get('width', 0.6) * dimensions.get('height', 2.0)
        face_velocity = flow_rate_m3s / filter_area if filter_area > 0 else 0
        k_factor = dimensions.get('k_factor', 25)  # Pa·s²/m²
        
        return k_factor * face_velocity**2
    
    elif component_type.lower() == 'coil':
        # Heat exchanger coil
        # More complex model based on coil geometry and flow rate
        rows = dimensions.get('rows', 4)
        fin_spacing = dimensions.get('fin_spacing', 2.0)  # mm
        face_area = dimensions.get('face_area', 1.2)  # m²
        
        # Calculate face velocity
        face_velocity = flow_rate_m3s / face_area if face_area > 0 else 0
        
        # Base pressure drop coefficient (increases with rows and decreases with fin spacing)
        base_coefficient = 15 * rows * (2.0 / fin_spacing)
        
        # Pressure drop increases with square of velocity
        return base_coefficient * face_velocity**2
    
    elif component_type.lower() == 'duct':
        # Duct pressure drop
        # Simplified model: ΔP = λ × (L/D) × (ρ × v²/2)
        length = dimensions.get('length', 1.0)  # m
        diameter = dimensions.get('diameter', 0.2)  # m
        roughness = dimensions.get('roughness', 0.0001)  # m
        air_density = dimensions.get('air_density', AIR_DENSITY_SEA_LEVEL)  # kg/m³
        
        # Calculate duct area and velocity
        area = math.pi * (diameter/2)**2
        velocity = flow_rate_m3s / area if area > 0 else 0
        
        # Calculate Reynolds number
        # Re = ρ × v × D / μ
        # Assuming air viscosity of 1.8e-5 Pa·s
        reynolds = air_density * velocity * diameter / 1.8e-5
        
        # Calculate friction factor using Colebrook-White equation
        # Simplified form
        if reynolds < 2300:  # Laminar flow
            friction_factor = 64 / reynolds if reynolds > 0 else 0.02
        else:  # Turbulent flow
            relative_roughness = roughness / diameter
            friction_factor = 0.25 / (math.log10(relative_roughness/3.7 + 5.74/reynolds**0.9))**2
        
        # Calculate pressure drop using Darcy-Weisbach equation
        return friction_factor * (length/diameter) * (air_density * velocity**2 / 2)
    
    elif component_type.lower() == 'rdx_door':
        # Rear door heat exchanger
        # Simplified model for entire door assembly
        doortype = dimensions.get('doortype', 'active')
        
        if doortype.lower() == 'passive':
            # Passive door (CL21 series)
            k_factor = 5.0  # Lower resistance in passive doors
        else:
            # Active door (CL20, CL23 series)
            k_factor = 3.0  # Typical value for active doors
            
        # Pressure drop increases with square of flow rate
        # Normalize to 1000 m³/h as reference
        normalized_flow = flow_rate / 1000
        
        return k_factor * normalized_flow**2 * 20  # Base: 20 Pa at 1000 m³/h
    
    else:
        # Default simplified quadratic model
        logger.warning(f"Component type '{component_type}' not recognized, using default model")
        k_factor = 10.0  # Default pressure drop coefficient
        normalized_flow = flow_rate / 3600
        
        return k_factor * normalized_flow**2

def system_curve(flow_rates: List[float], system_components: List[Dict[str, Any]]) -> List[float]:
    """
    Calculate system pressure curve based on components.
    
    Args:
        flow_rates: List of flow rates to calculate pressure drops for in m³/h
        system_components: List of dictionaries describing system components
        
    Returns:
        List of pressure drops corresponding to each flow rate
    """
    # Initialize pressure drops
    pressure_drops = [0.0] * len(flow_rates)
    
    # Calculate pressure drop for each flow rate
    for i, flow_rate in enumerate(flow_rates):
        total_drop = 0.0
        
        # Sum pressure drops from all components
        for component in system_components:
            component_type = component.get('type', 'default')
            dimensions = component.get('dimensions', {})
            
            total_drop += static_pressure_drop(flow_rate, component_type, dimensions)
        
        pressure_drops[i] = total_drop
    
    return pressure_drops

def fan_curve(flow_rates: List[float], nominal_flow: float, nominal_pressure: float,
             fan_speed_percentage: float = 100.0) -> List[float]:
    """
    Calculate fan pressure curve based on nominal values and speed.
    
    Args:
        flow_rates: List of flow rates to calculate pressures for in m³/h
        nominal_flow: Nominal flow rate in m³/h
        nominal_pressure: Nominal pressure in Pa
        fan_speed_percentage: Fan speed as percentage of maximum (0-100)
        
    Returns:
        List of pressures corresponding to each flow rate
    """
    # Simplified fan curve model: quadratic function
    # P = Pmax × (1 - (Q/Qmax)²)
    
    # Adjust Pmax based on fan speed
    pmax_adjusted = nominal_pressure * ((fan_speed_percentage / 100) ** 2)
    
    # Calculate pressures for each flow rate
    pressures = []
    for flow in flow_rates:
        flow_ratio = flow / nominal_flow if nominal_flow > 0 else 0
        pressure = pmax_adjusted * (1 - (flow_ratio ** 2))
        # Ensure pressure doesn't go negative
        pressures.append(max(0, pressure))
    
    return pressures

def find_operating_point(system_curve: List[float], fan_curve: List[float], 
                        flow_rates: List[float]) -> Tuple[float, float]:
    """
    Find the operating point where system curve intersects the fan curve.
    
    Args:
        system_curve: List of system pressures at each flow rate
        fan_curve: List of fan pressures at each flow rate
        flow_rates: List of flow rates
        
    Returns:
        Tuple of (flow_rate, pressure) at operating point
    """
    # Find the closest intersection point
    min_diff = float('inf')
    op_flow = 0.0
    op_pressure = 0.0
    
    for i, flow in enumerate(flow_rates):
        diff = abs(system_curve[i] - fan_curve[i])
        if diff < min_diff:
            min_diff = diff
            op_flow = flow
            op_pressure = (system_curve[i] + fan_curve[i]) / 2
    
    # Interpolate for more precise operating point
    # This is a simple linear interpolation between the two closest points
    # A more sophisticated method would use curve fitting
    
    return (op_flow, op_pressure)

def calculate_fan_power(flow_rate: float, pressure: float, efficiency: float = 0.6) -> float:
    """
    Calculate fan power consumption based on flow rate and pressure.
    
    Args:
        flow_rate: Flow rate in m³/h
        pressure: Pressure in Pa
        efficiency: Fan total efficiency (0-1)
        
    Returns:
        Power consumption in W
    """
    # Convert flow rate from m³/h to m³/s
    flow_rate_m3s = flow_rate / 3600
    
    # Calculate power
    # P = Q × ΔP / η
    power = (flow_rate_m3s * pressure) / efficiency
    
    return power

def fan_noise_level(base_noise: float, speed_ratio: float, distance: float = 1.0) -> float:
    """
    Calculate fan noise level based on speed and distance.
    
    Args:
        base_noise: Base noise level in dB(A) at reference conditions
        speed_ratio: Ratio of current speed to reference speed (0-1)
        distance: Distance from fan in meters
        
    Returns:
        Noise level in dB(A)
    """
    # Calculate speed-based noise increase
    # Noise increases with approximately 15*log10(N₂/N₁) dB
    speed_noise = 15 * math.log10(speed_ratio) if speed_ratio > 0 else -50
    
    # Calculate distance-based noise reduction
    # Noise decreases with approximately 20*log10(r) dB
    distance_attenuation = 20 * math.log10(distance) if distance > 0 else 0
    
    # Calculate total noise level
    noise_level = base_noise + speed_noise - distance_attenuation
    
    # Ensure noise level doesn't go below 0 dB
    return max(0, noise_level)

def multiple_fans_noise(individual_noise_levels: List[float]) -> float:
    """
    Calculate combined noise level from multiple fans.
    
    Args:
        individual_noise_levels: List of individual fan noise levels in dB(A)
        
    Returns:
        Combined noise level in dB(A)
    """
    # Sound pressure levels don't add linearly
    # We need to convert to energy, add, then convert back to dB
    
    # Convert dB to energy values
    energy_sum = sum(10 ** (noise / 10) for noise in individual_noise_levels)
    
    # Convert back to dB
    combined_noise = 10 * math.log10(energy_sum)
    
    return combined_noise

def airflow_uniformity(main_flow: float, branch_flows: List[float]) -> float:
    """
    Calculate airflow uniformity across parallel paths.
    
    Args:
        main_flow: Total airflow in m³/h
        branch_flows: List of branch airflows in m³/h
        
    Returns:
        Uniformity index (0-1) where 1 is perfectly uniform
    """
    if not branch_flows or main_flow <= 0:
        return 0
    
    # Calculate average branch flow
    average_flow = main_flow / len(branch_flows)
    
    # Calculate standard deviation
    variance = sum((flow - average_flow) ** 2 for flow in branch_flows) / len(branch_flows)
    std_dev = math.sqrt(variance)
    
    # Calculate coefficient of variation
    cv = std_dev / average_flow if average_flow > 0 else float('inf')
    
    # Convert to uniformity index (1 - CV, bounded to [0, 1])
    uniformity = 1 - min(1, cv)
    
    return uniformity

def air_changes_per_hour(air_flow: float, room_volume: float) -> float:
    """
    Calculate air changes per hour (ACH) for a room.
    
    Args:
        air_flow: Air flow rate in m³/h
        room_volume: Room volume in m³
        
    Returns:
        Air changes per hour
    """
    if room_volume <= 0:
        raise ValueError("Room volume must be greater than zero")
    
    return air_flow / room_volume
