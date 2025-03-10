"""
Unit conversion utilities for the Data Center Cooling Calculator.
"""


def convert_units(cooling_kw, room_temp, desired_temp, water_temp, from_units, to_units):
    """
    Convert temperature and cooling capacity between unit systems
    
    Args:
        cooling_kw (float): Cooling capacity
        room_temp (float): Room temperature
        desired_temp (float): Desired temperature
        water_temp (float): Water temperature
        from_units (str): Source unit system ('metric' or 'imperial')
        to_units (str): Target unit system ('metric' or 'imperial')
        
    Returns:
        tuple: (cooling_kw, room_temp, desired_temp, water_temp) in target units
    """
    if from_units == to_units:
        return cooling_kw, room_temp, desired_temp, water_temp
    
    if from_units == "imperial" and to_units == "metric":
        # Convert from imperial to metric
        cooling_kw_metric = tons_to_kw(cooling_kw)
        room_temp_metric = fahrenheit_to_celsius(room_temp)
        desired_temp_metric = fahrenheit_to_celsius(desired_temp)
        water_temp_metric = fahrenheit_to_celsius(water_temp)
        
        return cooling_kw_metric, room_temp_metric, desired_temp_metric, water_temp_metric
    
    elif from_units == "metric" and to_units == "imperial":
        # Convert from metric to imperial
        cooling_kw_imperial = kw_to_tons(cooling_kw)
        room_temp_imperial = celsius_to_fahrenheit(room_temp)
        desired_temp_imperial = celsius_to_fahrenheit(desired_temp)
        water_temp_imperial = celsius_to_fahrenheit(water_temp)
        
        return cooling_kw_imperial, room_temp_imperial, desired_temp_imperial, water_temp_imperial
    
    else:
        raise ValueError(f"Invalid unit conversion: {from_units} to {to_units}")


def celsius_to_fahrenheit(celsius):
    """
    Convert temperature from Celsius to Fahrenheit
    
    Args:
        celsius (float): Temperature in °C
        
    Returns:
        float: Temperature in °F
    """
    return celsius * 9/5 + 32


def fahrenheit_to_celsius(fahrenheit):
    """
    Convert temperature from Fahrenheit to Celsius
    
    Args:
        fahrenheit (float): Temperature in °F
        
    Returns:
        float: Temperature in °C
    """
    return (fahrenheit - 32) * 5/9


def kw_to_tons(kw):
    """
    Convert cooling capacity from kilowatts to tons of refrigeration
    
    Args:
        kw (float): Cooling capacity in kW
        
    Returns:
        float: Cooling capacity in tons
    """
    # 1 ton of refrigeration = 3.517 kW
    return kw / 3.517


def tons_to_kw(tons):
    """
    Convert cooling capacity from tons of refrigeration to kilowatts
    
    Args:
        tons (float): Cooling capacity in tons
        
    Returns:
        float: Cooling capacity in kW
    """
    # 1 ton of refrigeration = 3.517 kW
    return tons * 3.517


def m3h_to_gpm(m3h):
    """
    Convert flow rate from cubic meters per hour to US gallons per minute
    
    Args:
        m3h (float): Flow rate in m³/h
        
    Returns:
        float: Flow rate in GPM
    """
    # 1 m³/h = 4.403 GPM
    return m3h * 4.403


def gpm_to_m3h(gpm):
    """
    Convert flow rate from US gallons per minute to cubic meters per hour
    
    Args:
        gpm (float): Flow rate in GPM
        
    Returns:
        float: Flow rate in m³/h
    """
    # 1 GPM = 0.227 m³/h
    return gpm * 0.227


def m3h_to_cfm(m3h):
    """
    Convert air flow rate from cubic meters per hour to cubic feet per minute
    
    Args:
        m3h (float): Air flow rate in m³/h
        
    Returns:
        float: Air flow rate in CFM
    """
    # 1 m³/h = 0.589 CFM
    return m3h * 0.589


def cfm_to_m3h(cfm):
    """
    Convert air flow rate from cubic feet per minute to cubic meters per hour
    
    Args:
        cfm (float): Air flow rate in CFM
        
    Returns:
        float: Air flow rate in m³/h
    """
    # 1 CFM = 1.699 m³/h
    return cfm * 1.699


def kpa_to_psi(kpa):
    """
    Convert pressure from kilopascals to pounds per square inch
    
    Args:
        kpa (float): Pressure in kPa
        
    Returns:
        float: Pressure in PSI
    """
    # 1 kPa = 0.145 PSI
    return kpa * 0.145


def psi_to_kpa(psi):
    """
    Convert pressure from pounds per square inch to kilopascals
    
    Args:
        psi (float): Pressure in PSI
        
    Returns:
        float: Pressure in kPa
    """
    # 1 PSI = 6.895 kPa
    return psi * 6.895


def convert_result_units(result, to_units):
    """
    Convert all units in a calculation result
    
    Args:
        result (dict): Calculation result
        to_units (str): Target unit system ('metric' or 'imperial')
        
    Returns:
        dict: Result with converted units
    """
    if to_units == "metric":
        # Already in metric, no conversion needed
        return result
    
    # Convert to imperial
    converted = result.copy()
    
    # Convert input parameters
    if "input_parameters" in converted:
        params = converted["input_parameters"]
        if "cooling_kw" in params:
            params["cooling_tons"] = kw_to_tons(params.pop("cooling_kw"))
        if "room_temp" in params:
            params["room_temp_f"] = celsius_to_fahrenheit(params.pop("room_temp"))
        if "desired_temp" in params:
            params["desired_temp_f"] = celsius_to_fahrenheit(params.pop("desired_temp"))
        if "water_temp" in params:
            params["water_temp_f"] = celsius_to_fahrenheit(params.pop("water_temp"))
    
    # Convert water side data
    if "water_side" in converted:
        water = converted["water_side"]
        if "flow_rate" in water:
            water["flow_rate_gpm"] = m3h_to_gpm(water.pop("flow_rate"))
        if "temperature_in" in water:
            water["temperature_in_f"] = celsius_to_fahrenheit(water.pop("temperature_in"))
        if "temperature_out" in water:
            water["temperature_out_f"] = celsius_to_fahrenheit(water.pop("temperature_out"))
        if "delta_t" in water:
            water["delta_t_f"] = water.pop("delta_t") * 9/5  # Convert temperature difference
        if "pressure_drop" in water:
            water["pressure_drop_psi"] = kpa_to_psi(water.pop("pressure_drop"))
    
    # Convert air side data
    if "air_side" in converted:
        air = converted["air_side"]
        if "flow_rate" in air:
            air["flow_rate_cfm"] = m3h_to_cfm(air.pop("flow_rate"))
        if "temperature_in" in air:
            air["temperature_in_f"] = celsius_to_fahrenheit(air.pop("temperature_in"))
        if "temperature_out" in air:
            air["temperature_out_f"] = celsius_to_fahrenheit(air.pop("temperature_out"))
        if "delta_t" in air:
            air["delta_t_f"] = air.pop("delta_t") * 9/5  # Convert temperature difference
    
    # Convert heat transfer data
    if "heat_transfer" in converted:
        heat = converted["heat_transfer"]
        if "cooling_capacity" in heat:
            heat["cooling_capacity_tons"] = kw_to_tons(heat.pop("cooling_capacity"))
        if "lmtd" in heat:
            heat["lmtd_f"] = heat.pop("lmtd") * 9/5  # Convert temperature difference
    
    return converted 