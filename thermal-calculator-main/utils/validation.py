# utils/validation.py

"""
Validation utilities for the Data Center Cooling Calculator.

This module provides functions to validate input parameters against reasonable ranges
and product constraints.
"""

from typing import Dict, Any, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

# Define reasonable parameter ranges
PARAMETER_RANGES = {
    "cooling_kw": (0, 500),  # kW
    "room_temp": (10, 40),   # °C
    "desired_temp": (10, 35), # °C
    "water_temp": (5, 30),   # °C
    "flow_rate": (0, 50),    # m³/h
    "return_water_temp": (5, 50), # °C
    "fan_speed_percentage": (0, 100), # %
    "server_air_flow": (0, 20000), # m³/h
    "server_pressure": (0, 500), # Pa
    "glycol_percentage": (0, 60) # %
}

# Define valid options for categorical parameters
VALID_OPTIONS = {
    "fluid_type": ["water", "ethylene_glycol", "propylene_glycol"],
    "rack_type": ["42U600", "42U800", "48U800"],
    "units": ["metric", "imperial"]
}

def validate_input_parameters(cooling_kw: float, room_temp: float, desired_temp: float, 
                              water_temp: float, **kwargs) -> Dict[str, Any]:
    """
    Validate input parameters against reasonable ranges and constraints.
    
    Args:
        cooling_kw: Required cooling capacity in kW
        room_temp: Room temperature in °C
        desired_temp: Desired room temperature in °C
        water_temp: Water supply temperature in °C
        **kwargs: Additional optional parameters
        
    Returns:
        Dictionary with validation results:
            - valid: Whether all parameters are valid
            - message: Error message if not valid
            - warnings: List of warnings (parameters out of optimal range)
    """
    # Initialize result
    result = {
        "valid": True,
        "message": None,
        "warnings": []
    }
    
    # Validate required parameters
    required_params = {
        "cooling_kw": cooling_kw,
        "room_temp": room_temp,
        "desired_temp": desired_temp,
        "water_temp": water_temp
    }
    
    for param_name, param_value in required_params.items():
        if param_value is None:
            result["valid"] = False
            result["message"] = f"Required parameter {param_name} is missing"
            return result
            
        # Check if within reasonable range
        if param_name in PARAMETER_RANGES:
            min_val, max_val = PARAMETER_RANGES[param_name]
            if not min_val <= param_value <= max_val:
                result["valid"] = False
                result["message"] = f"Parameter {param_name} ({param_value}) is outside valid range ({min_val} to {max_val})"
                return result
    
    # Validate room temperature > desired temperature for cooling
    if room_temp <= desired_temp:
        result["valid"] = False
        result["message"] = f"Room temperature ({room_temp}°C) must be higher than desired temperature ({desired_temp}°C) for cooling"
        return result
    
    # Validate water temperature < desired temperature for cooling
    if water_temp >= desired_temp:
        result["valid"] = False
        result["message"] = f"Water temperature ({water_temp}°C) must be lower than desired temperature ({desired_temp}°C) for effective cooling"
        return result
    
    # Validate additional parameters if provided
    for param_name, param_value in kwargs.items():
        # Skip None values
        if param_value is None:
            continue
            
        # Check numerical parameters against ranges
        if param_name in PARAMETER_RANGES:
            min_val, max_val = PARAMETER_RANGES[param_name]
            try:
                param_value = float(param_value)  # Ensure numeric value
                if not min_val <= param_value <= max_val:
                    result["warnings"].append(f"Parameter {param_name} ({param_value}) is outside optimal range ({min_val} to {max_val})")
            except (ValueError, TypeError):
                result["valid"] = False
                result["message"] = f"Parameter {param_name} must be a number"
                return result
        
        # Check categorical parameters against valid options
        if param_name in VALID_OPTIONS:
            if param_value not in VALID_OPTIONS[param_name]:
                result["valid"] = False
                result["message"] = f"Parameter {param_name} ({param_value}) must be one of: {', '.join(VALID_OPTIONS[param_name])}"
                return result
    
    # Validate fluid type and glycol percentage
    if "fluid_type" in kwargs and kwargs["fluid_type"] != "water":
        if "glycol_percentage" in kwargs:
            glycol_percentage = kwargs["glycol_percentage"]
            if glycol_percentage <= 0:
                result["warnings"].append(f"Glycol percentage ({glycol_percentage}%) is too low for {kwargs['fluid_type']}. Consider using water instead.")
            elif glycol_percentage > 50:
                result["warnings"].append(f"High glycol percentage ({glycol_percentage}%) may significantly reduce heat transfer efficiency.")
    
    # Specific validation for passive cooling
    if kwargs.get("passive_preferred", False):
        if cooling_kw > 30:
            result["warnings"].append(f"Cooling requirement ({cooling_kw} kW) may exceed typical passive cooling capacity (30 kW). Active cooling might be required.")
    
    # Log validation result
    if not result["valid"]:
        logger.warning(f"Input validation failed: {result['message']}")
    elif result["warnings"]:
        logger.info(f"Input validation passed with warnings: {', '.join(result['warnings'])}")
    else:
        logger.debug("Input validation passed")
    
    return result

def validate_product_compatibility(product: Dict[str, Any], cooling_kw: float, 
                                  water_temp: float, **kwargs) -> Dict[str, Any]:
    """
    Validate whether a product is compatible with the cooling requirements.
    
    Args:
        product: Product data dictionary
        cooling_kw: Required cooling capacity in kW
        water_temp: Water supply temperature in °C
        **kwargs: Additional optional parameters
        
    Returns:
        Dictionary with validation results:
            - compatible: Whether the product is compatible
            - message: Explanation message
            - warnings: List of warnings
    """
    # Initialize result
    result = {
        "compatible": True,
        "message": "Product is compatible with requirements",
        "warnings": []
    }
    
    # Check cooling capacity
    if cooling_kw > product.get("max_cooling_capacity", 0):
        result["compatible"] = False
        result["message"] = f"Cooling requirement ({cooling_kw} kW) exceeds product capacity ({product.get('max_cooling_capacity', 0)} kW)"
        return result
    
    # Check if cooling requirement is too low (less than 20% of max capacity)
    if cooling_kw < product.get("max_cooling_capacity", 0) * 0.2:
        result["warnings"].append(f"Cooling requirement ({cooling_kw} kW) is significantly lower than product capacity ({product.get('max_cooling_capacity', 0)} kW). Consider a smaller unit for better efficiency.")
    
    # Check water temperature range
    water_specs = product.get("water_specs", {})
    min_water_temp = water_specs.get("min_inlet_temp", 0)
    max_water_temp = water_specs.get("max_inlet_temp", 100)
    
    if water_temp < min_water_temp:
        result["compatible"] = False
        result["message"] = f"Water temperature ({water_temp}°C) is below product minimum ({min_water_temp}°C)"
        return result
        
    if water_temp > max_water_temp:
        result["compatible"] = False
        result["message"] = f"Water temperature ({water_temp}°C) is above product maximum ({max_water_temp}°C)"
        return result
    
    # Check rack type compatibility if specified
    if "rack_type" in kwargs and kwargs["rack_type"] != product.get("rack_type", ""):
        result["compatible"] = False
        result["message"] = f"Product is designed for {product.get('rack_type', '')} racks, not {kwargs['rack_type']}"
        return result
    
    # Validation for passive cooling products (CL21 series)
    if product.get("series", "") == "CL21":
        # Passive systems have more stringent water temperature requirements
        if water_temp > 14:
            result["warnings"].append(f"Water temperature ({water_temp}°C) is above optimal for passive cooling (14°C). Cooling efficiency may be reduced.")
        
        # Passive systems need adequate server airflow
        if "server_air_flow" in kwargs:
            server_air_flow = kwargs["server_air_flow"]
            passive_specs = product.get("passive_specs", {})
            
            if server_air_flow < passive_specs.get("min_air_flow", 1000):
                result["compatible"] = False
                result["message"] = f"Server air flow ({server_air_flow} m³/h) is insufficient for passive cooling (min: {passive_specs.get('min_air_flow', 1000)} m³/h)"
                return result
    
    return result

# utils/unit_conversion.py

"""
Unit conversion utilities for the Data Center Cooling Calculator.

This module provides functions to convert between different units of measurement
for temperature, power, flow rates, and other physical quantities.
"""

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert temperature between Celsius and Fahrenheit.
    
    Args:
        value: Temperature value to convert
        from_unit: Source unit ('c' or 'f')
        to_unit: Target unit ('c' or 'f')
        
    Returns:
        Converted temperature value
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit == to_unit:
        return value
    
    if from_unit == 'c' and to_unit == 'f':
        return (value * 9/5) + 32
    
    if from_unit == 'f' and to_unit == 'c':
        return (value - 32) * 5/9
    
    raise ValueError(f"Unsupported temperature units: {from_unit} to {to_unit}")

def convert_power(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert power between different units (kW, ton, BTU/h).
    
    Args:
        value: Power value to convert
        from_unit: Source unit ('kw', 'ton', 'btu')
        to_unit: Target unit ('kw', 'ton', 'btu')
        
    Returns:
        Converted power value
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit == to_unit:
        return value
    
    # Convert to kW first (as common intermediate)
    kw_value = value
    
    if from_unit == 'ton':
        # 1 ton of refrigeration = 3.517 kW
        kw_value = value * 3.517
    elif from_unit == 'btu':
        # 1 BTU/h = 0.000293 kW
        kw_value = value * 0.000293
    
    # Convert from kW to target unit
    if to_unit == 'kw':
        return kw_value
    
    if to_unit == 'ton':
        # 1 kW = 0.284 tons of refrigeration
        return kw_value * 0.284
    
    if to_unit == 'btu':
        # 1 kW = 3412.14 BTU/h
        return kw_value * 3412.14
    
    raise ValueError(f"Unsupported power units: {from_unit} to {to_unit}")

def convert_flow_rate(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert flow rate between different units (m³/h, GPM, L/min).
    
    Args:
        value: Flow rate value to convert
        from_unit: Source unit ('m3h', 'gpm', 'lpm')
        to_unit: Target unit ('m3h', 'gpm', 'lpm')
        
    Returns:
        Converted flow rate value
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit == to_unit:
        return value
    
    # Convert to m³/h first (as common intermediate)
    m3h_value = value
    
    if from_unit == 'gpm':
        # 1 GPM = 0.227 m³/h
        m3h_value = value * 0.227
    elif from_unit == 'lpm':
        # 1 L/min = 0.06 m³/h
        m3h_value = value * 0.06
    
    # Convert from m³/h to target unit
    if to_unit == 'm3h':
        return m3h_value
    
    if to_unit == 'gpm':
        # 1 m³/h = 4.403 GPM
        return m3h_value * 4.403
    
    if to_unit == 'lpm':
        # 1 m³/h = 16.667 L/min
        return m3h_value * 16.667
    
    raise ValueError(f"Unsupported flow rate units: {from_unit} to {to_unit}")

def convert_pressure(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert pressure between different units (Pa, kPa, PSI, inWC).
    
    Args:
        value: Pressure value to convert
        from_unit: Source unit ('pa', 'kpa', 'psi', 'inwc')
        to_unit: Target unit ('pa', 'kpa', 'psi', 'inwc')
        
    Returns:
        Converted pressure value
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit == to_unit:
        return value
    
    # Convert to Pa first (as common intermediate)
    pa_value = value
    
    if from_unit == 'kpa':
        # 1 kPa = 1000 Pa
        pa_value = value * 1000
    elif from_unit == 'psi':
        # 1 PSI = 6894.76 Pa
        pa_value = value * 6894.76
    elif from_unit == 'inwc':
        # 1 inWC = 249.09 Pa
        pa_value = value * 249.09
    
    # Convert from Pa to target unit
    if to_unit == 'pa':
        return pa_value
    
    if to_unit == 'kpa':
        # 1 Pa = 0.001 kPa
        return pa_value * 0.001
    
    if to_unit == 'psi':
        # 1 Pa = 0.000145 PSI
        return pa_value * 0.000145
    
    if to_unit == 'inwc':
        # 1 Pa = 0.00401 inWC
        return pa_value * 0.00401
    
    raise ValueError(f"Unsupported pressure units: {from_unit} to {to_unit}")

def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert length between different units (mm, in, ft, m).
    
    Args:
        value: Length value to convert
        from_unit: Source unit ('mm', 'in', 'ft', 'm')
        to_unit: Target unit ('mm', 'in', 'ft', 'm')
        
    Returns:
        Converted length value
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit == to_unit:
        return value
    
    # Convert to mm first (as common intermediate)
    mm_value = value
    
    if from_unit == 'in':
        # 1 inch = 25.4 mm
        mm_value = value * 25.4
    elif from_unit == 'ft':
        # 1 foot = 304.8 mm
        mm_value = value * 304.8
    elif from_unit == 'm':
        # 1 meter = 1000 mm
        mm_value = value * 1000
    
    # Convert from mm to target unit
    if to_unit == 'mm':
        return mm_value
    
    if to_unit == 'in':
        # 1 mm = 0.0394 inches
        return mm_value * 0.0394
    
    if to_unit == 'ft':
        # 1 mm = 0.00328 feet
        return mm_value * 0.00328
    
    if to_unit == 'm':
        # 1 mm = 0.001 meters
        return mm_value * 0.001
    
    raise ValueError(f"Unsupported length units: {from_unit} to {to_unit}")

def convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert weight between different units (kg, lb).
    
    Args:
        value: Weight value to convert
        from_unit: Source unit ('kg', 'lb')
        to_unit: Target unit ('kg', 'lb')
        
    Returns:
        Converted weight value
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit == to_unit:
        return value
    
    if from_unit == 'kg' and to_unit == 'lb':
        # 1 kg = 2.20462 lb
        return value * 2.20462
    
    if from_unit == 'lb' and to_unit == 'kg':
        # 1 lb = 0.453592 kg
        return value * 0.453592
    
    raise ValueError(f"Unsupported weight units: {from_unit} to {to_unit}")

# utils/report_generator.py

"""
Report generation utilities for the Data Center Cooling Calculator.

This module provides functions to generate PDF reports with technical and commercial
information based on calculation results.
"""

from typing import Dict, Any
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_technical_report(data: Dict[str, Any], output_path: str) -> bool:
    """
    Generate a technical report based on calculation results.
    
    Args:
        data: Calculation results
        output_path: Path where to save the PDF report
        
    Returns:
        True if report was generated successfully, False otherwise
    """
    try:
        # This is a placeholder implementation that would be replaced with actual
        # PDF generation code using a library like ReportLab or WeasyPrint
        
        # For now, we'll just create a simple text file with the main information
        with open(output_path, 'w') as f:
            # Header
            f.write("===========================================\n")
            f.write("       TECHNICAL COOLING REPORT           \n")
            f.write("===========================================\n\n")
            
            # Date and time
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Product information
            product = data.get("product", {})
            f.write("PRODUCT INFORMATION\n")
            f.write("-----------------\n")
            f.write(f"Product: {product.get('name', 'N/A')}\n")
            f.write(f"Series: {product.get('series', 'N/A')}\n")
            f.write(f"Rack Type: {product.get('rack_type', 'N/A')}\n")
            f.write(f"Maximum Cooling Capacity: {product.get('max_cooling_capacity', 0)} kW\n\n")
            
            # Performance summary
            f.write("PERFORMANCE SUMMARY\n")
            f.write("------------------\n")
            f.write(f"Required Cooling: {data.get('cooling_capacity', 0)} kW\n")
            
            # Water-side parameters
            water_side = data.get("water_side", {})
            f.write("\nWATER-SIDE PARAMETERS\n")
            f.write("--------------------\n")
            f.write(f"Flow Rate: {water_side.get('flow_rate', 0):.2f} m³/h\n")
            f.write(f"Supply Temperature: {water_side.get('supply_temp', 0):.1f} °C\n")
            f.write(f"Return Temperature: {water_side.get('return_temp', 0):.1f} °C\n")
            f.write(f"Delta T: {water_side.get('delta_t', 0):.1f} °C\n")
            f.write(f"Pressure Drop: {water_side.get('pressure_drop', 0):.2f} kPa\n")
            
            # Air-side parameters
            air_side = data.get("air_side", {})
            f.write("\nAIR-SIDE PARAMETERS\n")
            f.write("------------------\n")
            
            if "fan_speed_percentage" in air_side:
                # Active cooling system
                f.write(f"Air Flow: {air_side.get('actual_air_flow', 0):.0f} m³/h\n")
                f.write(f"Fan Speed: {air_side.get('fan_speed_percentage', 0):.1f}%\n")
                f.write(f"Power Consumption: {air_side.get('power_consumption', 0):.1f} W\n")
                f.write(f"Noise Level: {air_side.get('noise_level', 0):.1f} dB(A)\n")
            else:
                # Passive cooling system
                f.write(f"Required Server Air Flow: {air_side.get('required_air_flow', 0):.0f} m³/h\n")
                f.write(f"Door Pressure Drop: {air_side.get('door_pressure_drop', 0):.1f} Pa\n")
                f.write(f"Power Consumption: 0 W (Passive System)\n")
            
            # Valve recommendation
            valve = data.get("valve_recommendation", {})
            f.write("\nVALVE RECOMMENDATION\n")
            f.write("-------------------\n")
            f.write(f"Valve Type: {valve.get('valve_type', 'N/A')}\n")
            f.write(f"Valve Size: {valve.get('valve_size', 'N/A')}\n")
            f.write(f"Max Flow Rate: {valve.get('max_flow_rate', 0):.1f} m³/h\n")
            f.write(f"Utilization: {valve.get('utilization_percentage', 0):.1f}%\n")
            
            # Recommended settings
            settings = valve.get("recommended_settings", {})
            f.write(f"Recommended Settings: {settings.get('min', 0):.0f}% to {settings.get('max', 0):.0f}%\n")
            
            # Efficiency metrics
            efficiency = data.get("efficiency", {})
            f.write("\nEFFICIENCY METRICS\n")
            f.write("-----------------\n")
            f.write(f"COP: {efficiency.get('cop', 0):.2f}\n")
            f.write(f"EER: {efficiency.get('eer', 0):.2f}\n")
            f.write(f"PUE: {efficiency.get('actual_pue', 0):.3f}\n")
            
            # Footer
            f.write("\n===========================================\n")
            f.write("End of Report\n")
        
        logger.info(f"Technical report generated: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating technical report: {str(e)}")
        return False

def generate_commercial_report(data: Dict[str, Any], output_path: str) -> bool:
    """
    Generate a commercial report based on calculation results.
    
    Args:
        data: Calculation results
        output_path: Path where to save the PDF report
        
    Returns:
        True if report was generated successfully, False otherwise
    """
    try:
        # This is a placeholder implementation that would be replaced with actual
        # PDF generation code using a library like ReportLab or WeasyPrint
        
        # For now, we'll just create a simple text file with the main information
        with open(output_path, 'w') as f:
            # Header
            f.write("===========================================\n")
            f.write("       COMMERCIAL COOLING REPORT          \n")
            f.write("===========================================\n\n")
            
            # Date and time
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Product information
            product = data.get("product", {})
            f.write("PRODUCT INFORMATION\n")
            f.write("-----------------\n")
            f.write(f"Product: {product.get('name', 'N/A')}\n")
            f.write(f"Series: {product.get('series', 'N/A')}\n\n")
            
            # Performance summary
            f.write("PERFORMANCE SUMMARY\n")
            f.write("------------------\n")
            f.write(f"Cooling Capacity: {data.get('cooling_capacity', 0)} kW\n")
            
            # Get commercial data
            commercial = data.get("commercial", {})
            
            if not commercial:
                f.write("\nNo commercial data available.\n")
                return True
            
            # Energy costs
            energy_costs = commercial.get("energy_costs", {})
            f.write("\nENERGY CONSUMPTION & COSTS\n")
            f.write("-------------------------\n")
            f.write(f"Power Consumption: {energy_costs.get('power_kw', 0):.3f} kW\n")
            f.write(f"Annual Energy: {energy_costs.get('annual_energy_kwh', 0):.0f} kWh\n")
            f.write(f"Annual Cost: ${energy_costs.get('annual_cost', 0):.2f}\n")
            
            # Comparison with traditional cooling
            traditional = commercial.get("traditional_energy_costs", {})
            f.write("\nCOMPARISON WITH TRADITIONAL COOLING\n")
            f.write("---------------------------------\n")
            f.write(f"Traditional Annual Energy: {traditional.get('annual_energy_kwh', 0):.0f} kWh\n")
            f.write(f"Traditional Annual Cost: ${traditional.get('annual_cost', 0):.2f}\n")
            f.write(f"Annual Savings: ${commercial.get('annual_savings', 0):.2f}\n")
            
            # ROI and TCO
            f.write("\nINVESTMENT ANALYSIS\n")
            f.write("------------------\n")
            f.write(f"Estimated Capital Cost: ${commercial.get('capital_cost', 0):.2f}\n")
            f.write(f"ROI: {commercial.get('roi_percentage', 0):.1f}%\n")
            f.write(f"Payback Period: {commercial.get('payback_years', 0):.1f} years\n")
            
            # Environmental impact
            environmental = commercial.get("environmental", {})
            f.write("\nENVIRONMENTAL IMPACT\n")
            f.write("-------------------\n")
            f.write(f"Annual Carbon Emissions: {environmental.get('annual_carbon_kg', 0):.0f} kg CO₂\n")
            f.write(f"Tree Equivalent: {environmental.get('tree_equivalent', 0):.0f} trees\n")
            f.write(f"Car Equivalent: {environmental.get('car_equivalent', 0):.1f} cars\n")
            
            # Footer
            f.write("\n===========================================\n")
            f.write("End of Report\n")
        
        logger.info(f"Commercial report generated: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating commercial report: {str(e)}")
        return False
