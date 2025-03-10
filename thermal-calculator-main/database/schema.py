# database/schema.py

"""
This module defines the database schemas for the data center cooling calculator.
These schemas define the structure of the data used by the calculator.
"""

import json
import os
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

# Product Database Schema
PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "id": {"type": "string"},
        "rack_type": {"type": "string"},
        "max_cooling_capacity": {"type": "number"},
        "number_of_fans": {"type": "integer"},
        "coil_geometry": {
            "type": "object",
            "properties": {
                "tube_diameter": {"type": "number"},
                "tube_length": {"type": "number"},
                "tube_rows": {"type": "integer"},
                "fin_spacing": {"type": "number"},
                "fin_thickness": {"type": "number"},
                "fin_area": {"type": "number"},
                "number_of_passes": {"type": "integer"}
            },
            "required": ["tube_diameter", "tube_length", "tube_rows", "fin_spacing", 
                        "fin_thickness", "fin_area", "number_of_passes"]
        },
        "fan_specs": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "nominal_air_flow": {"type": "number"},
                "nominal_static_pressure": {"type": "number"},
                "nominal_power": {"type": "number"},
                "nominal_noise": {"type": "number"},
                "max_air_flow": {"type": "number"},
                "max_static_pressure": {"type": "number"}
            },
            "required": ["model", "nominal_air_flow", "nominal_static_pressure", 
                        "nominal_power", "nominal_noise", "max_air_flow", "max_static_pressure"]
        },
        "controller_specs": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "min_voltage": {"type": "number"},
                "max_voltage": {"type": "number"},
                "voltage_step": {"type": "number"},
                "control_type": {"type": "string"}
            },
            "required": ["model", "min_voltage", "max_voltage", "voltage_step", "control_type"]
        },
        "valve_options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "size": {"type": "string"},
                    "max_flow_rate": {"type": "number"},
                    "kv_value": {"type": "number"}
                },
                "required": ["type", "size", "max_flow_rate", "kv_value"]
            }
        },
        "dimensions": {
            "type": "object",
            "properties": {
                "height": {"type": "number"},
                "width": {"type": "number"},
                "depth": {"type": "number"},
                "weight": {"type": "number"}
            },
            "required": ["height", "width", "depth", "weight"]
        },
        "part_number": {"type": "string"},
        "fast_track": {"type": "boolean"}
    },
    "required": ["name", "id", "rack_type", "max_cooling_capacity", "number_of_fans", 
               "coil_geometry", "fan_specs", "controller_specs", "valve_options", "dimensions"]
}

# Regional Data Schema
REGIONAL_SCHEMA = {
    "type": "object",
    "properties": {
        "global": {
            "type": "object",
            "properties": {
                "ashrae": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "temp_recommended": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"}
                                }
                            },
                            "humidity_recommended": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "additionalProperties": {
            "type": "object",
            "properties": {
                "energy_costs": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                },
                "carbon_factors": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                },
                "efficiency_metric": {"type": "string"},
                "regulations": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "default_voltage": {"type": "number"},
                "default_fluid": {"type": "string"},
                "default_glycol_percentage": {"type": "number"},
                "preferred_units": {"type": "string"},
                "free_cooling_potential": {"type": "string"},
                "ambient_temp": {
                    "type": "object",
                    "properties": {
                        "min": {"type": "number"},
                        "max": {"type": "number"}
                    }
                },
                "humidity": {
                    "type": "object",
                    "properties": {
                        "min": {"type": "number"},
                        "max": {"type": "number"}
                    }
                },
                "dew_point_concerns": {"type": "string"},
                "water_min_temp": {"type": "number"}
            }
        }
    }
}

# Fluid Properties Schema
FLUID_PROPERTIES_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "temperatures": {
            "type": "array",
            "items": {"type": "number"}
        },
        "properties": {
            "type": "object",
            "properties": {
                "density": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "specific_heat": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "viscosity": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "thermal_conductivity": {
                    "type": "array",
                    "items": {"type": "number"}
                }
            },
            "required": ["density", "specific_heat", "viscosity", "thermal_conductivity"]
        },
        "concentrations": {
            "type": "array",
            "items": {"type": "number"}
        },
        "concentration_factors": {
            "type": "object",
            "properties": {
                "density": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "specific_heat": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "viscosity": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "thermal_conductivity": {
                    "type": "array",
                    "items": {"type": "number"}
                }
            }
        },
        "freezing_points": {
            "type": "array",
            "items": {"type": "number"}
        }
    },
    "required": ["name", "temperatures", "properties"]
}

class DatabaseManager:
    """
    Manages the database for the cooling calculator.
    
    This class provides methods for loading, validating, and accessing the
    product database, regional settings, and fluid properties.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the database manager.
        
        Args:
            data_dir: Directory containing database files
        """
        self.data_dir = data_dir
        
        # Initialize databases
        self.products = {}
        self.regional_data = {}
        self.fluid_properties = {}
        
        # Validator function
        self.validator = None
    
    def load_databases(self) -> bool:
        """
        Load all databases.
        
        Returns:
            True if all databases loaded successfully, False otherwise
        """
        products_loaded = self.load_product_database('products.json')
        regional_loaded = self.load_regional_database('regional_settings.json')
        fluids_loaded = self.load_fluid_properties('fluid_properties.json')
        
        return products_loaded and regional_loaded and fluids_loaded
    
    def load_product_database(self, filename: str) -> bool:
        """
        Load product database from file.
        
        Args:
            filename: Name of product database file
            
        Returns:
            True if database loaded successfully, False otherwise
        """
        logger.info(f"Loading product database: {filename}")
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Validate data
            if self.validator:
                # If jsonschema validator is available, use it
                self.validator.validate(data, PRODUCT_SCHEMA)
            
            # Convert list to dictionary with id as key
            if isinstance(data, list):
                self.products = {product['id']: product for product in data}
            else:
                self.products = data
                
            logger.info(f"Loaded {len(self.products)} products")
            return True
            
        except Exception as e:
            logger.error(f"Error loading product database: {str(e)}")
            return False
    
    def load_regional_database(self, filename: str) -> bool:
        """
        Load regional settings database from file.
        
        Args:
            filename: Name of regional settings file
            
        Returns:
            True if database loaded successfully, False otherwise
        """
        logger.info(f"Loading regional database: {filename}")
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                self.regional_data = json.load(f)
            
            # Validate data
            if self.validator:
                # If jsonschema validator is available, use it
                self.validator.validate(self.regional_data, REGIONAL_SCHEMA)
                
            logger.info(f"Loaded regional settings for {len(self.regional_data) - 1} regions")  # -1 for 'global'
            return True
            
        except Exception as e:
            logger.error(f"Error loading regional database: {str(e)}")
            return False
    
    def load_fluid_properties(self, filename: str) -> bool:
        """
        Load fluid properties database from file.
        
        Args:
            filename: Name of fluid properties file
            
        Returns:
            True if database loaded successfully, False otherwise
        """
        logger.info(f"Loading fluid properties: {filename}")
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Validate data
            if self.validator:
                # If jsonschema validator is available, use it
                for fluid in data:
                    self.validator.validate(fluid, FLUID_PROPERTIES_SCHEMA)
            
            # Convert list to dictionary with name as key
            if isinstance(data, list):
                self.fluid_properties = {fluid['name']: fluid for fluid in data}
            else:
                self.fluid_properties = data
                
            logger.info(f"Loaded properties for {len(self.fluid_properties)} fluids")
            return True
            
        except Exception as e:
            logger.error(f"Error loading fluid properties: {str(e)}")
            return False
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product dictionary or None if not found
        """
        return self.products.get(product_id)
    
    def get_products_by_rack_type(self, rack_type: str) -> List[Dict[str, Any]]:
        """
        Get products by rack type.
        
        Args:
            rack_type: Rack type
            
        Returns:
            List of product dictionaries
        """
        return [product for product in self.products.values() 
                if product.get('rack_type') == rack_type]
    
    def get_fast_track_products(self) -> List[Dict[str, Any]]:
        """
        Get fast track products.
        
        Returns:
            List of fast track product dictionaries
        """
        return [product for product in self.products.values() 
                if product.get('fast_track', False)]
    
    def get_regional_settings(self, region: str, subregion: Optional[str] = None) -> Dict[str, Any]:
        """
        Get regional settings.
        
        Args:
            region: Region name
            subregion: Subregion name (optional)
            
        Returns:
            Dictionary containing regional settings
        """
        settings = self.regional_data.get('global', {}).copy()
        
        if region in self.regional_data:
            # Update with region-specific settings
            self._deep_update(settings, self.regional_data[region])
            
            # Update with subregion-specific settings if applicable
            if subregion and isinstance(self.regional_data[region], dict) and subregion in self.regional_data[region]:
                self._deep_update(settings, self.regional_data[region][subregion])
        
        return settings
    
    def get_fluid_properties(self, fluid_name: str) -> Optional[Dict[str, Any]]:
        """
        Get fluid properties.
        
        Args:
            fluid_name: Fluid name
            
        Returns:
            Dictionary containing fluid properties or None if not found
        """
        return self.fluid_properties.get(fluid_name)
    
    def get_fluid_property_at_temperature(self, fluid_name: str, property_name: str, 
                                         temperature: float, 
                                         concentration: Optional[float] = None) -> Optional[float]:
        """
        Get fluid property at specific temperature and concentration.
        
        Args:
            fluid_name: Fluid name
            property_name: Property name (density, specific_heat, viscosity, thermal_conductivity)
            temperature: Temperature in °C
            concentration: Concentration percentage (0-100) for mixtures
            
        Returns:
            Property value or None if not found
        """
        fluid = self.get_fluid_properties(fluid_name)
        if not fluid:
            return None
        
        # Get property values at different temperatures
        if property_name not in fluid.get('properties', {}):
            return None
            
        property_values = fluid['properties'][property_name]
        temperatures = fluid.get('temperatures', [])
        
        if not property_values or not temperatures or len(property_values) != len(temperatures):
            return None
            
        # Interpolate property value at the specified temperature
        property_value = self._interpolate(temperatures, property_values, temperature)
        
        # Apply concentration factor if applicable
        if concentration and concentration > 0 and 'concentration_factors' in fluid:
            # Get concentration factors
            if property_name not in fluid['concentration_factors']:
                return property_value
                
            concentration_factors = fluid['concentration_factors'][property_name]
            concentrations = fluid.get('concentrations', [])
            
            if not concentration_factors or not concentrations or len(concentration_factors) != len(concentrations):
                return property_value
                
            # Interpolate concentration factor
            factor = self._interpolate(concentrations, concentration_factors, concentration)
            
            # Apply factor
            property_value *= factor
        
        return property_value
    
    def _interpolate(self, x_values: List[float], y_values: List[float], x: float) -> float:
        """
        Linearly interpolate a value.
        
        Args:
            x_values: List of x values
            y_values: List of y values
            x: x value to interpolate at
            
        Returns:
            Interpolated y value
        """
        # Check if x is below the range
        if x <= x_values[0]:
            return y_values[0]
            
        # Check if x is above the range
        if x >= x_values[-1]:
            return y_values[-1]
            
        # Find the two closest x values
        for i in range(len(x_values) - 1):
            if x_values[i] <= x <= x_values[i + 1]:
                # Linear interpolation
                x1, x2 = x_values[i], x_values[i + 1]
                y1, y2 = y_values[i], y_values[i + 1]
                
                return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
        
        # This should not happen
        return y_values[0]
    
    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep update a dictionary.
        
        Args:
            d: Dictionary to update
            u: Dictionary with updates
            
        Returns:
            Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
                
        return d

# Sample Product Database
SAMPLE_PRODUCT_DATABASE = [
    {
        "id": "CL20C14_42U600",
        "name": "Cold Logic CL20 C14 42U 600mm Wide",
        "rack_type": "42U600",
        "max_cooling_capacity": 35.0,  # kW
        "number_of_fans": 4,
        "coil_geometry": {
            "tube_diameter": 12.0,  # mm
            "tube_length": 1.2,  # m
            "tube_rows": 4,
            "fin_spacing": 2.0,  # mm
            "fin_thickness": 0.15,  # mm
            "fin_area": 2.8,  # m²
            "number_of_passes": 4
        },
        "fan_specs": {
            "model": "Fan Model A",
            "nominal_air_flow": 2500.0,  # m³/h
            "nominal_static_pressure": 50.0,  # Pa
            "nominal_power": 45.0,  # W
            "nominal_noise": 52.0,  # dB(A)
            "max_air_flow": 3000.0,  # m³/h
            "max_static_pressure": 75.0  # Pa
        },
        "controller_specs": {
            "model": "Controller Model X",
            "min_voltage": 0.0,  # V
            "max_voltage": 10.0,  # V
            "voltage_step": 0.1,  # V
            "control_type": "variable voltage"
        },
        "valve_options": [
            {
                "type": "2way",
                "size": "DN 25",
                "max_flow_rate": 6.3,  # m³/h
                "kv_value": 10.0
            },
            {
                "type": "2way",
                "size": "DN 32",
                "max_flow_rate": 10.0,  # m³/h
                "kv_value": 16.0
            },
            {
                "type": "epiv",
                "size": "DN 25",
                "max_flow_rate": 4.8,  # m³/h
                "kv_value": 8.6
            },
            {
                "type": "epiv",
                "size": "DN 32",
                "max_flow_rate": 9.5,  # m³/h
                "kv_value": 15.0
            }
        ],
        "dimensions": {
            "height": 2000.0,  # mm
            "width": 600.0,  # mm
            "depth": 200.0,  # mm
            "weight": 45.0  # kg
        },
        "part_number": "CL20C14-42U600",
        "fast_track": True
    },
    {
        "id": "CL20C14_42U800",
        "name": "Cold Logic CL20 C14 42U 800mm Wide",
        "rack_type": "42U800",
        "max_cooling_capacity": 60.0,  # kW
        "number_of_fans": 5,
        "coil_geometry": {
            "tube_diameter": 12.0,  # mm
            "tube_length": 1.6,  # m
            "tube_rows": 4,
            "fin_spacing": 2.0,  # mm
            "fin_thickness": 0.15,  # mm
            "fin_area": 3.7,  # m²
            "number_of_passes": 4
        },
        "fan_specs": {
            "model": "Fan Model B",
            "nominal_air_flow": 3000.0,  # m³/h
            "nominal_static_pressure": 55.0,  # Pa
            "nominal_power": 50.0,  # W
            "nominal_noise": 54.0,  # dB(A)
            "max_air_flow": 3600.0,  # m³/h
            "max_static_pressure": 80.0  # Pa
        },
        "controller_specs": {
            "model": "Controller Model X",
            "min_voltage": 0.0,  # V
            "max_voltage": 10.0,  # V
            "voltage_step": 0.1,  # V
            "control_type": "variable voltage"
        },
        "valve_options": [
            {
                "type": "2way",
                "size": "DN 25",
                "max_flow_rate": 6.3,  # m³/h
                "kv_value": 10.0
            },
            {
                "type": "2way",
                "size": "DN 32",
                "max_flow_rate": 10.0,  # m³/h
                "kv_value": 16.0
            },
            {
                "type": "epiv",
                "size": "DN 25",
                "max_flow_rate": 4.8,  # m³/h
                "kv_value": 8.6
            },
            {
                "type": "epiv",
                "size": "DN 32",
                "max_flow_rate": 9.5,  # m³/h
                "kv_value": 15.0
            }
        ],
        "dimensions": {
            "height": 2000.0,  # mm
            "width": 800.0,  # mm
            "depth": 200.0,  # mm
            "weight": 55.0  # kg
        },
        "part_number": "CL20C14-42U800",
        "fast_track": True
    },
    {
        "id": "CL20C14_48U800",
        "name": "Cold Logic CL20 C14 48U 800mm Wide",
        "rack_type": "48U800",
        "max_cooling_capacity": 80.0,  # kW
        "number_of_fans": 6,
        "coil_geometry": {
            "tube_diameter": 12.0,  # mm
            "tube_length": 1.8,  # m
            "tube_rows": 4,
            "fin_spacing": 2.0,  # mm
            "fin_thickness": 0.15,  # mm
            "fin_area": 4.2,  # m²
            "number_of_passes": 4
        },
        "fan_specs": {
            "model": "Fan Model C",
            "nominal_air_flow": 3500.0,  # m³/h
            "nominal_static_pressure": 60.0,  # Pa
            "nominal_power": 55.0,  # W
            "nominal_noise": 56.0,  # dB(A)
            "max_air_flow": 4200.0,  # m³/h
            "max_static_pressure": 85.0  # Pa
        },
        "controller_specs": {
            "model": "Controller Model X",
            "min_voltage": 0.0,  # V
            "max_voltage": 10.0,  # V
            "voltage_step": 0.1,  # V
            "control_type": "variable voltage"
        },
        "valve_options": [
            {
                "type": "2way",
                "size": "DN 32",
                "max_flow_rate": 10.0,  # m³/h
                "kv_value": 16.0
            },
            {
                "type": "2way",
                "size": "DN 40",
                "max_flow_rate": 16.0,  # m³/h
                "kv_value": 25.0
            },
            {
                "type": "epiv",
                "size": "DN 32",
                "max_flow_rate": 9.5,  # m³/h
                "kv_value": 15.0
            },
            {
                "type": "epiv",
                "size": "DN 40",
                "max_flow_rate": 15.0,  # m³/h
                "kv_value": 24.0
            }
        ],
        "dimensions": {
            "height": 2200.0,  # mm
            "width": 800.0,  # mm
            "depth": 200.0,  # mm
            "weight": 65.0  # kg
        },
        "part_number": "CL20C14-48U800",
        "fast_track": True
    },
    {
        "id": "CL18C20_48U800",
        "name": "Cold Logic CL18 C20 48U 800mm Wide",
        "rack_type": "48U800",
        "max_cooling_capacity": 100.0,  # kW
        "number_of_fans": 6,
        "coil_geometry": {
            "tube_diameter": 12.0,  # mm
            "tube_length": 1.8,  # m
            "tube_rows": 6,
            "fin_spacing": 1.8,  # mm
            "fin_thickness": 0.15,  # mm
            "fin_area": 4.8,  # m²
            "number_of_passes": 6
        },
        "fan_specs": {
            "model": "Fan Model D",
            "nominal_air_flow": 4000.0,  # m³/h
            "nominal_static_pressure": 65.0,  # Pa
            "nominal_power": 60.0,  # W
            "nominal_noise": 58.0,  # dB(A)
            "max_air_flow": 4800.0,  # m³/h
            "max_static_pressure": 90.0  # Pa
        },
        "controller_specs": {
            "model": "Controller Model X",
            "min_voltage": 0.0,  # V
            "max_voltage": 10.0,  # V
            "voltage_step": 0.1,  # V
            "control_type": "variable voltage"
        },
        "valve_options": [
            {
                "type": "2way",
                "size": "DN 40",
                "max_flow_rate": 16.0,  # m³/h
                "kv_value": 25.0
            },
            {
                "type": "2way",
                "size": "DN 50",
                "max_flow_rate": 25.0,  # m³/h
                "kv_value": 40.0
            },
            {
                "type": "epiv",
                "size": "DN 40",
                "max_flow_rate": 15.0,  # m³/h
                "kv_value": 24.0
            },
            {
                "type": "epiv",
                "size": "DN 50",
                "max_flow_rate": 24.0,  # m³/h
                "kv_value": 38.0
            }
        ],
        "dimensions": {
            "height": 2200.0,  # mm
            "width": 800.0,  # mm
            "depth": 200.0,  # mm
            "weight": 70.0  # kg
        },
        "part_number": "CL18C20-48U800",
        "fast_track": True
    }
]

# Sample Regional Settings
SAMPLE_REGIONAL_SETTINGS = {
    "global": {
        "ashrae": {
            "class_a1": {
                "temp_recommended": {"min": 18, "max": 27},  # °C
                "humidity_recommended": {"min": 40, "max": 60},  # % RH
            },
            "class_a2": {
                "temp_recommended": {"min": 18, "max": 27},  # °C
                "humidity_recommended": {"min": 35, "max": 70},  # % RH
            },
            "class_a3": {
                "temp_recommended": {"min": 18, "max": 27},  # °C
                "humidity_recommended": {"min": 30, "max": 80},  # % RH
            },
            "class_a4": {
                "temp_recommended": {"min": 18, "max": 27},  # °C
                "humidity_recommended": {"min": 20, "max": 80},  # % RH
            }
        }
    },
    
    "europe": {
        "energy_costs": {"electricity": 0.20},  # €/kWh
        "carbon_factors": {"electricity": 0.275},  # kg CO2/kWh (EU average)
        "efficiency_metric": "SEER",  # Seasonal Energy Efficiency Ratio
        "regulations": ["EU Code of Conduct for Data Centers", "EN 50600"],
        "default_voltage": 230,
        "default_fluid": "water",
    },
    
    "north_america": {
        "energy_costs": {"electricity": 0.15},  # $/kWh
        "carbon_factors": {"electricity": 0.417},  # kg CO2/kWh (US average)
        "efficiency_metric": "IEER",  # Integrated Energy Efficiency Ratio
        "regulations": ["ASHRAE 90.4", "ENERGY STAR for Data Centers"],
        "default_voltage": 208,
        "default_fluid": "water",
        "preferred_units": "imperial",
    },
    
    "nordic": {
        "energy_costs": {"electricity": 0.10},  # €/kWh
        "carbon_factors": {"electricity": 0.028},  # kg CO2/kWh (Norway example)
        "default_fluid": "propylene_glycol",  # As mentioned in transcript
        "default_glycol_percentage": 30,
        "free_cooling_potential": "high",
    },
    
    "asia_pacific": {
        "energy_costs": {"electricity": 0.18},  # $/kWh (average)
        "carbon_factors": {"electricity": 0.408},  # kg CO2/kWh (average)
        "regulations": ["SS 564", "Green Mark for Data Centers"],
        "dew_point_concerns": "high",
        
        "singapore": {
            "energy_costs": {"electricity": 0.18},  # S$/kWh
            "carbon_factors": {"electricity": 0.408},  # kg CO2/kWh
            "regulations": ["SS 564", "Green Mark for Data Centers"],
            "ambient_temp": {"min": 25, "max": 32},
            "humidity": {"min": 70, "max": 90},
            "dew_point_concerns": "high",
            "water_min_temp": 18,  # As mentioned in transcript
        }
    }
}

# Sample Fluid Properties
SAMPLE_FLUID_PROPERTIES = [
    {
        "name": "water",
        "temperatures": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],  # °C
        "properties": {
            "density": [999.8, 999.7, 998.2, 995.7, 992.2, 988.1, 983.2, 977.8, 971.8, 965.3, 958.4],  # kg/m³
            "specific_heat": [4.217, 4.191, 4.182, 4.178, 4.178, 4.181, 4.184, 4.190, 4.196, 4.205, 4.216],  # kJ/kg·K
            "viscosity": [1.792, 1.307, 1.002, 0.798, 0.653, 0.547, 0.467, 0.404, 0.355, 0.315, 0.282],  # mPa·s
            "thermal_conductivity": [0.561, 0.580, 0.598, 0.615, 0.630, 0.644, 0.656, 0.665, 0.673, 0.679, 0.683]  # W/m·K
        }
    },
    {
        "name": "ethylene_glycol",
        "temperatures": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],  # °C
        "properties": {
            "density": [1130.8, 1125.6, 1120.0, 1114.4, 1108.6, 1102.2, 1095.6, 1088.8, 1081.8, 1074.4, 1067.0],  # kg/m³
            "specific_heat": [2.294, 2.323, 2.355, 2.387, 2.418, 2.450, 2.482, 2.513, 2.545, 2.576, 2.608],  # kJ/kg·K
            "viscosity": [57.2, 28.91, 15.85, 9.414, 5.984, 4.057, 2.886, 2.143, 1.641, 1.293, 1.041],  # mPa·s
            "thermal_conductivity": [0.242, 0.246, 0.249, 0.252, 0.255, 0.258, 0.261, 0.264, 0.267, 0.270, 0.273]  # W/m·K
        },
        "concentrations": [0, 10, 20, 30, 40, 50, 60],  # %
        "concentration_factors": {
            "density": [1.0, 1.02, 1.03, 1.05, 1.07, 1.09, 1.10],
            "specific_heat": [1.0, 0.97, 0.94, 0.91, 0.88, 0.84, 0.80],
            "viscosity": [1.0, 1.1, 1.3, 1.8, 2.4, 3.8, 5.7],
            "thermal_conductivity": [1.0, 0.97, 0.93, 0.89, 0.84, 0.79, 0.74]
        },
        "freezing_points": [0, -3, -8, -15, -24, -36, -52]  # °C
    },
    {
        "name": "propylene_glycol",
        "temperatures": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],  # °C
        "properties": {
            "density": [1050.2, 1045.3, 1040.2, 1035.0, 1029.6, 1024.0, 1018.2, 1012.2, 1006.0, 999.6, 993.0],  # kg/m³
            "specific_heat": [2.512, 2.536, 2.561, 2.587, 2.613, 2.639, 2.665, 2.690, 2.716, 2.741, 2.767],  # kJ/kg·K
            "viscosity": [243.0, 99.35, 46.4, 24.33, 14.0, 8.743, 5.767, 3.999, 2.899, 2.191, 1.713],  # mPa·s
            "thermal_conductivity": [0.191, 0.195, 0.200, 0.204, 0.208, 0.212, 0.217, 0.221, 0.225, 0.229, 0.233]  # W/m·K
        },
        "concentrations": [0, 10, 20, 30, 40, 50, 60],  # %
        "concentration_factors": {
            "density": [1.0, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06],
            "specific_heat": [1.0, 0.97, 0.95, 0.92, 0.88, 0.84, 0.79],
            "viscosity": [1.0, 1.2, 1.5, 2.2, 3.2, 5.2, 8.6],
            "thermal_conductivity": [1.0, 0.96, 0.91, 0.86, 0.81, 0.76, 0.70]
        },
        "freezing_points": [0, -3, -7, -13, -21, -33, -48]  # °C
    }
]
