# database/regional_data.py

"""
Regional data module for the Data Center Cooling Calculator.

This module provides functions for accessing and managing regional settings
and standards, including ASHRAE guidelines, energy costs, and environmental factors.
"""

import os
import json
import copy
import logging
from typing import Dict, Any, List, Optional, Union

from utils.config import get_config

logger = logging.getLogger(__name__)

# ASHRAE Data Center Classifications
ASHRAE_CLASSES = {
    "A1": {
        "temp_recommended": {"min": 18, "max": 27},  # °C
        "humidity_recommended": {"min": 40, "max": 60},  # % RH
        "temp_allowable": {"min": 15, "max": 32},  # °C
        "humidity_allowable": {"min": 20, "max": 80},  # % RH
        "max_dew_point": 17,  # °C
        "description": "Enterprise servers, storage products"
    },
    "A2": {
        "temp_recommended": {"min": 18, "max": 27},  # °C
        "humidity_recommended": {"min": 35, "max": 70},  # % RH
        "temp_allowable": {"min": 10, "max": 35},  # °C
        "humidity_allowable": {"min": 20, "max": 80},  # % RH
        "max_dew_point": 21,  # °C
        "description": "Volume servers, storage products, personal computers, workstations"
    },
    "A3": {
        "temp_recommended": {"min": 18, "max": 27},  # °C
        "humidity_recommended": {"min": 30, "max": 80},  # % RH
        "temp_allowable": {"min": 5, "max": 40},  # °C
        "humidity_allowable": {"min": 8, "max": 85},  # % RH
        "max_dew_point": 24,  # °C
        "description": "IT equipment, point-of-sale, ruggedized controllers"
    },
    "A4": {
        "temp_recommended": {"min": 18, "max": 27},  # °C
        "humidity_recommended": {"min": 20, "max": 80},  # % RH
        "temp_allowable": {"min": 5, "max": 45},  # °C
        "humidity_allowable": {"min": 8, "max": 90},  # % RH
        "max_dew_point": 24,  # °C
        "description": "Point-of-sale equipment, ruggedized controllers, PDAs"
    }
}

# Base Regional Data
REGIONAL_DATA = {
    "global": {
        "ashrae": ASHRAE_CLASSES,
        "default_voltage": 230,  # V
        "default_fluid": "water",
        "default_glycol_percentage": 0,
        "energy_costs": {"electricity": 0.15},  # $/kWh
        "carbon_factors": {"electricity": 0.5},  # kg CO2/kWh
        "reference_pue": 1.8  # Reference PUE for traditional cooling
    },
    
    "europe": {
        "energy_costs": {"electricity": 0.20},  # €/kWh
        "carbon_factors": {"electricity": 0.275},  # kg CO2/kWh (EU average)
        "efficiency_metric": "SEER",  # Seasonal Energy Efficiency Ratio
        "regulations": ["EU Code of Conduct for Data Centers", "EN 50600"],
        "default_voltage": 230,  # V
        "default_fluid": "water",
        "currency": "EUR",
        "ambient_temp": {"min": 10, "max": 25},  # °C (typical)
        "humidity": {"min": 40, "max": 70},  # % RH (typical)
        "dew_point_concerns": "moderate",
        "free_cooling_potential": "moderate",
        "water_availability": "good",
        "subregions": {
            "uk": {
                "energy_costs": {"electricity": 0.22},  # £/kWh
                "carbon_factors": {"electricity": 0.233},  # kg CO2/kWh
                "currency": "GBP",
                "ambient_temp": {"min": 7, "max": 20},  # °C (typical)
                "regulations": ["EU Code of Conduct for Data Centers", "EN 50600", "UK Climate Change Agreement"]
            },
            "germany": {
                "energy_costs": {"electricity": 0.23},  # €/kWh
                "carbon_factors": {"electricity": 0.338},  # kg CO2/kWh
                "currency": "EUR",
                "ambient_temp": {"min": 5, "max": 24}  # °C (typical)
            },
            "france": {
                "energy_costs": {"electricity": 0.17},  # €/kWh
                "carbon_factors": {"electricity": 0.056},  # kg CO2/kWh (low due to nuclear)
                "currency": "EUR",
                "ambient_temp": {"min": 8, "max": 25}  # °C (typical)
            }
        }
    },
    
    "north_america": {
        "energy_costs": {"electricity": 0.15},  # $/kWh
        "carbon_factors": {"electricity": 0.417},  # kg CO2/kWh (US average)
        "efficiency_metric": "IEER",  # Integrated Energy Efficiency Ratio
        "regulations": ["ASHRAE 90.4", "ENERGY STAR for Data Centers"],
        "default_voltage": 208,  # V
        "default_fluid": "water",
        "preferred_units": "imperial",
        "currency": "USD",
        "ambient_temp": {"min": 10, "max": 30},  # °C (typical)
        "humidity": {"min": 30, "max": 60},  # % RH (typical)
        "dew_point_concerns": "moderate",
        "free_cooling_potential": "moderate",
        "water_availability": "varied",
        "subregions": {
            "west_coast": {
                "energy_costs": {"electricity": 0.18},  # $/kWh
                "carbon_factors": {"electricity": 0.227},  # kg CO2/kWh
                "ambient_temp": {"min": 15, "max": 30},  # °C (typical)
                "free_cooling_potential": "good"
            },
            "east_coast": {
                "energy_costs": {"electricity": 0.16},  # $/kWh
                "carbon_factors": {"electricity": 0.302},  # kg CO2/kWh
                "ambient_temp": {"min": 5, "max": 32},  # °C (typical)
                "humidity": {"min": 40, "max": 80}  # % RH (typical)
            },
            "midwest": {
                "energy_costs": {"electricity": 0.12},  # $/kWh
                "carbon_factors": {"electricity": 0.614},  # kg CO2/kWh
                "ambient_temp": {"min": -15, "max": 35},  # °C (typical, wider range)
                "free_cooling_potential": "excellent"
            }
        }
    },
    
    "nordic": {
        "energy_costs": {"electricity": 0.10},  # €/kWh
        "carbon_factors": {"electricity": 0.028},  # kg CO2/kWh (Norway example)
        "default_fluid": "propylene_glycol",  # As mentioned in transcript
        "default_glycol_percentage": 30,
        "free_cooling_potential": "high",
        "currency": "EUR",
        "ambient_temp": {"min": -10, "max": 20},  # °C (typical)
        "humidity": {"min": 30, "max": 70},  # % RH (typical)
        "dew_point_concerns": "low",
        "water_availability": "excellent",
        "subregions": {
            "norway": {
                "energy_costs": {"electricity": 0.08},  # NOK/kWh (converted)
                "carbon_factors": {"electricity": 0.011},  # kg CO2/kWh
                "currency": "NOK",
                "ambient_temp": {"min": -15, "max": 20}  # °C (typical)
            },
            "sweden": {
                "energy_costs": {"electricity": 0.09},  # SEK/kWh (converted)
                "carbon_factors": {"electricity": 0.013},  # kg CO2/kWh
                "currency": "SEK",
                "ambient_temp": {"min": -10, "max": 22}  # °C (typical)
            },
            "finland": {
                "energy_costs": {"electricity": 0.11},  # €/kWh
                "carbon_factors": {"electricity": 0.093},  # kg CO2/kWh
                "currency": "EUR",
                "ambient_temp": {"min": -20, "max": 25}  # °C (typical)
            }
        }
    },
    
    "asia_pacific": {
        "energy_costs": {"electricity": 0.18},  # $/kWh (average)
        "carbon_factors": {"electricity": 0.408},  # kg CO2/kWh (average)
        "regulations": ["SS 564", "Green Mark for Data Centers"],
        "dew_point_concerns": "high",
        "currency": "USD",
        "ambient_temp": {"min": 18, "max": 35},  # °C (typical)
        "humidity": {"min": 50, "max": 90},  # % RH (typical)
        "free_cooling_potential": "limited",
        "water_availability": "varied",
        "subregions": {
            "singapore": {
                "energy_costs": {"electricity": 0.18},  # S$/kWh
                "carbon_factors": {"electricity": 0.408},  # kg CO2/kWh
                "regulations": ["SS 564", "Green Mark for Data Centers"],
                "ambient_temp": {"min": 25, "max": 32},
                "humidity": {"min": 70, "max": 90},
                "dew_point_concerns": "high",
                "water_min_temp": 18,  # As mentioned in transcript
                "currency": "SGD"
            },
            "japan": {
                "energy_costs": {"electricity": 0.22},  # JPY/kWh (converted)
                "carbon_factors": {"electricity": 0.57},  # kg CO2/kWh
                "ambient_temp": {"min": 5, "max": 35},  # °C (typical)
                "humidity": {"min": 40, "max": 80},  # % RH (typical)
                "currency": "JPY"
            },
            "australia": {
                "energy_costs": {"electricity": 0.25},  # AU$/kWh
                "carbon_factors": {"electricity": 0.79},  # kg CO2/kWh
                "ambient_temp": {"min": 15, "max": 45},  # °C (typical)
                "humidity": {"min": 20, "max": 60},  # % RH (typical)
                "preferred_units": "metric",
                "currency": "AUD"
            }
        }
    },
    
    "middle_east": {
        "energy_costs": {"electricity": 0.08},  # $/kWh (average, often subsidized)
        "carbon_factors": {"electricity": 0.718},  # kg CO2/kWh (average)
        "ambient_temp": {"min": 20, "max": 50},  # °C (typical)
        "humidity": {"min": 10, "max": 90},  # % RH (varies widely)
        "dew_point_concerns": "variable",
        "free_cooling_potential": "very limited",
        "water_availability": "limited",
        "currency": "USD",
        "default_fluid": "water",  # Generally water is still preferred despite conditions
        "subregions": {
            "uae": {
                "energy_costs": {"electricity": 0.08},  # AED/kWh (converted)
                "carbon_factors": {"electricity": 0.644},  # kg CO2/kWh
                "ambient_temp": {"min": 20, "max": 48},  # °C (typical)
                "humidity": {"min": 30, "max": 90},  # % RH (typical, higher near coast)
                "currency": "AED"
            },
            "saudi_arabia": {
                "energy_costs": {"electricity": 0.05},  # SAR/kWh (converted)
                "carbon_factors": {"electricity": 0.825},  # kg CO2/kWh
                "ambient_temp": {"min": 15, "max": 50},  # °C (typical)
                "humidity": {"min": 10, "max": 50},  # % RH (typical, lower inland)
                "water_availability": "very limited",
                "currency": "SAR"
            }
        }
    }
}

def load_regional_data(data_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load regional data from file or use default data.
    
    Args:
        data_file: Path to regional data file (optional)
        
    Returns:
        Dictionary containing regional data
    """
    # Use default data if no file specified
    if not data_file:
        return REGIONAL_DATA
    
    # Check if file exists
    if not os.path.exists(data_file):
        logger.warning(f"Regional data file not found: {data_file}, using default data")
        return REGIONAL_DATA
    
    try:
        # Load data from file
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Validate data structure
        if not isinstance(data, dict) or "global" not in data:
            logger.warning("Invalid regional data format, using default data")
            return REGIONAL_DATA
        
        logger.info(f"Loaded regional data from {data_file}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading regional data: {str(e)}")
        return REGIONAL_DATA

def get_regional_settings(data: Dict[str, Any], region: str, 
                         subregion: Optional[str] = None) -> Dict[str, Any]:
    """
    Get settings for a specific region and optional subregion.
    
    This function applies hierarchical inheritance of settings from global to region to subregion.
    
    Args:
        data: Regional data dictionary
        region: Region name
        subregion: Subregion name (optional)
        
    Returns:
        Dictionary containing regional settings
    """
    # Start with global settings
    settings = copy.deepcopy(data.get("global", {}))
    
    # Apply region-specific settings if available
    if region in data:
        region_data = data[region]
        settings = _deep_update(settings, region_data)
        
        # Apply subregion-specific settings if available
        if subregion and "subregions" in region_data and subregion in region_data["subregions"]:
            subregion_data = region_data["subregions"][subregion]
            settings = _deep_update(settings, subregion_data)
    else:
        logger.warning(f"Region not found: {region}, using global settings")
    
    return settings

def get_all_regions(data: Dict[str, Any]) -> List[str]:
    """
    Get a list of all available regions.
    
    Args:
        data: Regional data dictionary
        
    Returns:
        List of region names
    """
    return [region for region in data.keys() if region != "global"]

def get_subregions(data: Dict[str, Any], region: str) -> List[str]:
    """
    Get a list of all available subregions for a region.
    
    Args:
        data: Regional data dictionary
        region: Region name
        
    Returns:
        List of subregion names
    """
    if region in data and "subregions" in data[region]:
        return list(data[region]["subregions"].keys())
    return []

def get_ashrae_class(data: Dict[str, Any], class_name: str) -> Dict[str, Any]:
    """
    Get ASHRAE classification data.
    
    Args:
        data: Regional data dictionary
        class_name: ASHRAE class name (e.g., "A1", "A2")
        
    Returns:
        Dictionary containing ASHRAE class data
    """
    global_data = data.get("global", {})
    ashrae_data = global_data.get("ashrae", {})
    
    if class_name in ashrae_data:
        return ashrae_data[class_name]
    
    logger.warning(f"ASHRAE class not found: {class_name}")
    return {}

def validate_conditions(temp: float, humidity: float, class_name: str,
                      data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate temperature and humidity against ASHRAE requirements.
    
    Args:
        temp: Temperature in °C
        humidity: Relative humidity in %
        class_name: ASHRAE class name (e.g., "A1", "A2")
        data: Regional data dictionary
        
    Returns:
        Dictionary containing validation results
    """
    ashrae_class = get_ashrae_class(data, class_name)
    
    if not ashrae_class:
        return {
            "valid": False,
            "message": f"Unknown ASHRAE class: {class_name}",
            "in_recommended": False,
            "in_allowable": False
        }
    
    # Check recommended range
    temp_rec = ashrae_class.get("temp_recommended", {})
    humidity_rec = ashrae_class.get("humidity_recommended", {})
    
    in_recommended = (
        temp_rec.get("min", 0) <= temp <= temp_rec.get("max", 100) and
        humidity_rec.get("min", 0) <= humidity <= humidity_rec.get("max", 100)
    )
    
    # Check allowable range
    temp_allow = ashrae_class.get("temp_allowable", {})
    humidity_allow = ashrae_class.get("humidity_allowable", {})
    
    in_allowable = (
        temp_allow.get("min", 0) <= temp <= temp_allow.get("max", 100) and
        humidity_allow.get("min", 0) <= humidity <= humidity_allow.get("max", 100)
    )
    
    # Check dew point (simplified calculation)
    dew_point = calculate_dew_point(temp, humidity)
    max_dew_point = ashrae_class.get("max_dew_point", 100)
    dew_point_ok = dew_point <= max_dew_point
    
    # Determine validity
    valid = in_allowable and dew_point_ok
    
    # Generate message
    if valid:
        if in_recommended:
            message = f"Conditions are within ASHRAE {class_name} recommended range"
        else:
            message = f"Conditions are within ASHRAE {class_name} allowable range, but outside recommended range"
    else:
        if dew_point_ok:
            message = f"Conditions are outside ASHRAE {class_name} allowable range"
        else:
            message = f"Dew point ({dew_point:.1f}°C) exceeds maximum ({max_dew_point}°C) for ASHRAE {class_name}"
    
    return {
        "valid": valid,
        "message": message,
        "in_recommended": in_recommended,
        "in_allowable": in_allowable,
        "dew_point": dew_point,
        "dew_point_ok": dew_point_ok,
        "temp_recommended": temp_rec,
        "humidity_recommended": humidity_rec,
        "temp_allowable": temp_allow,
        "humidity_allowable": humidity_allow
    }

def calculate_dew_point(temp: float, relative_humidity: float) -> float:
    """
    Calculate dew point temperature using Magnus approximation.
    
    Args:
        temp: Temperature in °C
        relative_humidity: Relative humidity in %
        
    Returns:
        Dew point temperature in °C
    """
    # Constants for Magnus approximation
    a = 17.27
    b = 237.7
    
    # Calculate alpha
    alpha = ((a * temp) / (b + temp)) + math.log(relative_humidity / 100.0)
    
    # Calculate dew point
    dew_point = (b * alpha) / (a - alpha)
    
    return dew_point

def _deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively update a dictionary with values from another dictionary.
    
    Args:
        target: Target dictionary to update
        source: Source dictionary with new values
        
    Returns:
        Updated dictionary
    """
    for key, value in source.items():
        if key == "subregions":
            # Skip subregions when updating
            continue
            
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            # Recursively update nested dictionaries
            target[key] = _deep_update(target[key], value)
        else:
            # Update or add value
            target[key] = value
    
    return target

def get_climate_data(region: str, subregion: Optional[str] = None) -> Dict[str, Any]:
    """
    Get climate data for a specific region and subregion.
    
    Args:
        region: Region name
        subregion: Subregion name (optional)
        
    Returns:
        Dictionary containing climate data
    """
    # Load regional data
    data_file = get_config("regional_data_file")
    data = load_regional_data(data_file)
    
    # Get regional settings
    settings = get_regional_settings(data, region, subregion)
    
    # Extract climate data
    climate_data = {
        "ambient_temp": settings.get("ambient_temp", {"min": 15, "max": 30}),
        "humidity": settings.get("humidity", {"min": 30, "max": 70}),
        "dew_point_concerns": settings.get("dew_point_concerns", "moderate"),
        "free_cooling_potential": settings.get("free_cooling_potential", "moderate")
    }
    
    return climate_data

def get_commercial_data(region: str, subregion: Optional[str] = None) -> Dict[str, Any]:
    """
    Get commercial data for a specific region and subregion.
    
    Args:
        region: Region name
        subregion: Subregion name (optional)
        
    Returns:
        Dictionary containing commercial data
    """
    # Load regional data
    data_file = get_config("regional_data_file")
    data = load_regional_data(data_file)
    
    # Get regional settings
    settings = get_regional_settings(data, region, subregion)
    
    # Extract commercial data
    commercial_data = {
        "energy_costs": settings.get("energy_costs", {"electricity": 0.15}),
        "carbon_factors": settings.get("carbon_factors", {"electricity": 0.5}),
        "currency": settings.get("currency", "USD"),
        "reference_pue": settings.get("reference_pue", 1.8)
    }
    
    return commercial_data

def get_technical_defaults(region: str, subregion: Optional[str] = None) -> Dict[str, Any]:
    """
    Get technical defaults for a specific region and subregion.
    
    Args:
        region: Region name
        subregion: Subregion name (optional)
        
    Returns:
        Dictionary containing technical defaults
    """
    # Load regional data
    data_file = get_config("regional_data_file")
    data = load_regional_data(data_file)
    
    # Get regional settings
    settings = get_regional_settings(data, region, subregion)
    
    # Extract technical defaults
    technical_defaults = {
        "default_voltage": settings.get("default_voltage", 230),
        "default_fluid": settings.get("default_fluid", "water"),
        "default_glycol_percentage": settings.get("default_glycol_percentage", 0),
        "preferred_units": settings.get("preferred_units", "metric"),
        "water_min_temp": settings.get("water_min_temp", 10)
    }
    
    return technical_defaults
