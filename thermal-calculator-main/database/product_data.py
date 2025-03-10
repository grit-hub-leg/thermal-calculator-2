# database/product_data.py

"""
Product database for ColdLogik cooling products based on provided specifications.
This module defines the product database that will be used by the cooling calculator.
"""

from typing import Dict, Any

# ColdLogik Product Database
COLDLOGIK_PRODUCTS = [
    # CL20 Series - Standard Rear Door Heat Exchanger
    {
        "id": "CL20_42U600",
        "name": "ColdLogik CL20 Rear Door Heat Exchanger 42U 600mm",
        "series": "CL20",
        "description": "Standard rear door heat exchanger for data center cooling",
        "rack_type": "42U600",
        "max_cooling_capacity": 65.0,  # kW
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
            "model": "EC Fan",
            "nominal_air_flow": 6847.0,  # m³/h
            "max_air_flow": 8217.0,  # m³/h
            "nominal_static_pressure": 55.0,  # Pa
            "nominal_power": 60.0,  # W per fan
            "nominal_noise": 54.0,  # dB(A)
            "max_static_pressure": 80.0  # Pa
        },
        "controller_specs": {
            "model": "ColdLogik Controller",
            "min_voltage": 0.0,  # V
            "max_voltage": 10.0,  # V
            "voltage_step": 0.1,  # V
            "control_type": "variable voltage",
            "protocols": ["Modbus", "BACnet", "SNMP"],
            "supports_rms": True  # Room Management System support
        },
        "water_specs": {
            "min_inlet_temp": 14.0,  # °C
            "max_inlet_temp": 21.0,  # °C
            "nominal_delta_t": 5.0,  # °C
            "min_flow_rate": 1.0,  # m³/h
            "recommended_flow_rate": 4.0  # m³/h
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
            "height": 2040.0,  # mm
            "width": 596.0,  # mm
            "depth": 380.0,  # mm
            "wet_weight": 145.0  # kg
        },
        "electrical": {
            "max_current": 12.5,  # A
            "voltage": 230.0,  # V
            "phases": 1
        },
        "efficiency": {
            "min_pue": 1.03,
            "eer": 80.0,
            "operational_savings": 0.86  # 86% compared to traditional cooling
        },
        "ashrae_compliant": "A1",
        "part_number": "CL20-42U600",
        "fast_track": True
    },
    {
        "id": "CL20_42U800",
        "name": "ColdLogik CL20 Rear Door Heat Exchanger 42U 800mm",
        "series": "CL20",
        "description": "Standard rear door heat exchanger for data center cooling",
        "rack_type": "42U800",
        "max_cooling_capacity": 75.0,  # kW
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
            "model": "EC Fan",
            "nominal_air_flow": 7500.0,  # m³/h
            "max_air_flow": 8217.0,  # m³/h
            "nominal_static_pressure": 55.0,  # Pa
            "nominal_power": 60.0,  # W per fan
            "nominal_noise": 54.0,  # dB(A)
            "max_static_pressure": 80.0  # Pa
        },
        "controller_specs": {
            "model": "ColdLogik Controller",
            "min_voltage": 0.0,  # V
            "max_voltage": 10.0,  # V
            "voltage_step": 0.1,  # V
            "control_type": "variable voltage",
            "protocols": ["Modbus", "BACnet", "SNMP"],
            "supports_rms": True  # Room Management System support
        },
        "water_specs": {
            "min_inlet_temp": 14.0,  # °C
            "max_inlet_temp": 21.0,  # °C
            "nominal_delta_t": 5.0,  # °C
            "min_flow_rate": 1.5,  # m³/h
            "recommended_flow_rate": 5.0  # m³/h
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
            "height": 2040.0,  # mm
            "width": 796.0,  # mm
            "depth": 380.0,  # mm
            "wet_weight": 170.0  # kg
        },
        "electrical": {
            "max_current": 12.5,  # A
            "voltage": 230.0,  # V
            "phases": 1
        },
        "efficiency": {
            "min_pue": 1.03,
            "eer": 80.0,
            "operational_savings": 0.86  # 86% compared to traditional cooling
        },
        "ashrae_compliant": "A1",
        "part_number": "CL20-42U800",
        "fast_track": True
    },
    {
        "id": "CL20_48U800",
        "name": "ColdLogik CL20 Rear Door Heat Exchanger 48U 800mm",
        "series": "CL20",
        "description": "Standard rear door heat exchanger for data center cooling",
        "rack_type": "48U800",
        "max_cooling_capacity": 93.0,  # kW
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
            "model": "EC Fan",
            "nominal_air_flow": 8217.0,  # m³/h
            "max_air_flow": 8217.0,  # m³/h
            "nominal_static_pressure": 60.0,  # Pa
            "nominal_power": 60.0,  # W per fan
            "nominal_noise": 56.0,  # dB(A)
            "max_static_pressure": 85.0  # Pa
        },
        "controller_specs": {
            "model": "ColdLogik Controller",
            "min_voltage": 0.0,  # V
            "max_voltage": 10.0,  # V
            "voltage_step": 0.1,  # V
            "control_type": "variable voltage",
            "protocols": ["Modbus", "BACnet", "SNMP"],
            "supports_rms": True  # Room Management System support
        },
        "water_specs": {
            "min_inlet_temp": 14.0,  # °C
            "max_inlet_temp": 21.0,  # °C
            "nominal_delta_t": 5.0,  # °C
            "min_flow_rate": 2.0,  # m³/h
            "recommended_flow_rate": 6.5  # m³/h
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
            "height": 2485.0,  # mm
            "width": 796.0,  # mm
            "depth": 380.0,  # mm
            "wet_weight": 192.0  # kg
        },
        "electrical": {
            "max_current": 12.5,  # A
            "voltage": 230.0,  # V
            "phases": 1
        },
        "efficiency": {
            "min_pue": 1.03,
            "eer": 80.0,
            "operational_savings": 0.86  # 86% compared to traditional cooling
        },
        "ashrae_compliant": "A1",
        "part_number": "CL20-48U800",
        "fast_track": True
    },
    
    # CL21 Series - Smart Passive Rear Door Heat Exchanger
    {
        "id": "CL21_42U600",
        "name": "ColdLogik CL21 Smart Passive RDHx 42U 600mm",
        "series": "CL21",
        "description": "Passive rear door heat exchanger with zero energy requirements",
        "rack_type": "42U600",
        "max_cooling_capacity": 20.0,  # kW
        "number_of_fans": 0,  # Passive system, no fans
        "coil_geometry": {
            "tube_diameter": 12.0,  # mm
            "tube_length": 1.2,  # m
            "tube_rows": 6,
            "fin_spacing": 1.8,  # mm
            "fin_thickness": 0.15,  # mm
            "fin_area": 3.0,  # m²
            "number_of_passes": 6
        },
        "passive_specs": {
            "min_air_flow": 1000.0,  # m³/h
            "max_air_flow": 4000.0,  # m³/h
            "required_server_pressure": 20.0,  # Pa
        },
        "water_specs": {
            "min_inlet_temp": 14.0,  # °C
            "max_inlet_temp": 14.0,  # °C (Passive systems are more temperature sensitive)
            "nominal_delta_t": 6.0,  # °C
            "min_flow_rate": 1.0,  # m³/h
            "recommended_flow_rate": 3.0  # m³/h
        },
        "valve_options": [
            {
                "type": "2way",
                "size": "DN 25",
                "max_flow_rate": 6.3,  # m³/h
                "kv_value": 10.0
            },
            {
                "type": "epiv",
                "size": "DN 25",
                "max_flow_rate": 4.8,  # m³/h
                "kv_value": 8.6
            }
        ],
        "dimensions": {
            "height": 2000.0,  # mm
            "width": 597.0,  # mm
            "depth": 198.0,  # mm
            "wet_weight": 100.0  # kg
        },
        "electrical": {
            "max_current": 0.0,  # A (Passive system)
            "voltage": 0.0,  # V (Passive system)
            "phases": 0
        },
        "efficiency": {
            "min_pue": 1.01,  # Extremely efficient due to zero energy for cooling
            "eer": float('inf'),  # Infinite EER (no energy consumption)
            "operational_savings": 1.0  # 100% compared to traditional cooling
        },
        "ashrae_compliant": "A1",
        "part_number": "CL21-42U600",
        "fast_track": True
    },
    {
        "id": "CL21_42U800",
        "name": "ColdLogik CL21 Smart Passive RDHx 42U 800mm",
        "series": "CL21",
        "description": "Passive rear door heat exchanger with zero energy requirements",
        "rack_type": "42U800",
        "max_cooling_capacity": 25.0,  # kW
        "number_of_fans": 0,  # Passive system, no fans
        "coil_geometry": {
            "tube_diameter": 12.0,  # mm
            "tube_length": 1.6,  # m
            "tube_rows": 6,
            "fin_spacing": 1.8,  # mm
            "fin_thickness": 0.15,  # mm
            "fin_area": 4.0,  # m²
            "number_of_passes": 6
        },
        "passive_specs": {
            "min_air_flow": 1000.0,  # m³/h
            "max_air_flow": 5000.0,  # m³/h
            "required_server_pressure": 20.0,  # Pa
        },
        "water_specs": {
            "min_inlet_temp": 14.0,  # °C
            "max_inlet_temp": 14.0,  # °C (Passive systems are more temperature sensitive)
            "nominal_delta_t": 6.0,  # °C
            "min_flow_rate": 1.5,  # m³/h
            "recommended_flow_rate": 3.5  # m³/h
        },
        "valve_options": [
            {
                "type": "2way",
                "size": "DN 25",
                "max_flow_rate": 6.3,  # m³/h
                "kv_value": 10.0
            },
            {
                "type": "epiv",
                "size": "DN 25",
                "max_flow_rate": 4.8,  # m³/h
                "kv_value": 8.6
            }
        ],
        "dimensions": {
            "height": 2000.0,  # mm
            "width": 797.0,  # mm
            "depth": 198.0,  # mm
            "wet_weight": 115.0  # kg
        },
        "electrical": {
            "max_current": 0.0,  # A (Passive system)
            "voltage": 0.0,  # V (Passive system)
            "phases": 0
        },
        "efficiency": {
            "min_pue": 1.01,  # Extremely efficient due to zero energy for cooling
            "eer": float('inf'),  # Infinite EER (no energy consumption)
            "operational_savings": 1.0  # 100% compared to traditional cooling
        },
        "ashrae_compliant": "A1",
        "part_number": "CL21-42U800",
        "fast_track": True
    },
    {
        "id": "CL21_48U800",
        "name": "ColdLogik CL21 Smart Passive RDHx 48U 800mm",
        "series": "CL21",
        "description": "Passive rear door heat exchanger with zero energy requirements",
        "rack_type": "48U800",
        "max_cooling_capacity": 29.0,  # kW
        "number_of_fans": 0,  # Passive system, no fans
        "coil_geometry": {
            "tube_diameter": 12.0,  # mm
            "tube_length": 1.8,  # m
            "tube_rows": 6,
            "fin_spacing": 1.8,  # mm
            "fin_thickness": 0.15,  # mm
            "fin_area": 4.5,  # m²
            "number_of_passes": 6
        },
        "passive_specs": {
            "min_air_flow": 1000.0,  # m³/h
            "max_air_flow": 6000.0,  # m³/h
            "required_server_pressure": 20.0,  # Pa
        },
        "water_specs": {
            "min_inlet_temp": 14.0,  # °C
            "max_inlet_temp": 14.0,  # °C (Passive systems are more temperature sensitive)
            "nominal_delta_t": 6.0,  # °C
            "min_flow_rate": 2.0,  # m³/h
            "recommended_flow_rate": 4.0  # m³/h
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
            "height": 2444.0,  # mm
            "width": 797.0,  # mm
            "depth": 198.0,  # mm
            "wet_weight": 125.0  # kg
        },
        "electrical": {
            "max_current": 0.0,  # A (Passive system)
            "voltage": 0.0,  # V (Passive system)
            "phases": 0
        },
        "efficiency": {
            "min_pue": 1.01,  # Extremely efficient due to zero energy for cooling
            "eer": float('inf'),  # Infinite EER (no energy consumption)
            "operational_savings": 1.0  # 100% compared to traditional cooling
        },
        "ashrae_compliant": "A1",
        "part_number": "CL21-48U800",
        "fast_track": True
    },
    
    # CL23 Series - High-Performance Computing (HPC) Rear Door Heat Exchanger
    {
        "id": "CL23_48U800",
        "name": "ColdLogik CL23 HPC RDHx 48U 800mm",
        "series": "CL23",
        "description": "High-performance cooling rear door heat exchanger for HPC environments",
        "rack_type": "48U800",
        "max_cooling_capacity": 204.0,  # kW (extremely high capacity)
        "number_of_fans": 8,  # Higher fan count for increased airflow
        "coil_geometry": {
            "tube_diameter": 12.0,  # mm
            "tube_length": 1.8,  # m
            "tube_rows": 8,
            "fin_spacing": 1.6,  # mm
            "fin_thickness": 0.15,  # mm
            "fin_area": 5.5,  # m²
            "number_of_passes": 8
        },
        "fan_specs": {
            "model": "High-Performance EC Fan",
            "nominal_air_flow": 14229.0,  # m³/h
            "max_air_flow": 16000.0,  # m³/h
            "nominal_static_pressure": 80.0,  # Pa
            "nominal_power": 120.0,  # W per fan
            "nominal_noise": 60.0,  # dB(A)
            "max_static_pressure": 120.0  # Pa
        },
        "controller_specs": {
            "model": "ColdLogik HPC Controller",
            "min_voltage": 0.0,  # V
            "max_voltage": 10.0,  # V
            "voltage_step": 0.1,  # V
            "control_type": "variable voltage",
            "protocols": ["Modbus", "BACnet", "SNMP"],
            "supports_rms": True  # Room Management System support
        },
        "water_specs": {
            "min_inlet_temp": 14.0,  # °C
            "max_inlet_temp": 23.0,  # °C
            "nominal_delta_t": 7.0,  # °C
            "min_flow_rate": 4.0,  # m³/h
            "recommended_flow_rate": 12.0  # m³/h
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
            "height": 2481.0,  # mm
            "width": 799.0,  # mm
            "depth": 415.0,  # mm
            "wet_weight": 185.0  # kg
        },
        "electrical": {
            "max_current": 16.0,  # A
            "voltage": 230.0,  # V
            "phases": 1
        },
        "efficiency": {
            "min_pue": 1.035,
            "eer": 100.0,  # Very high EER
            "operational_savings": 0.92  # 92% compared to traditional cooling
        },
        "ashrae_compliant": "A1",
        "part_number": "CL23-48U800",
        "fast_track": True
    }
]

def get_products_by_series(series: str) -> list:
    """Get products by series name (CL20, CL21, CL23)."""
    return [p for p in COLDLOGIK_PRODUCTS if p["series"] == series]

def get_product_by_id(product_id: str) -> Dict[str, Any]:
    """Get a specific product by its ID."""
    for product in COLDLOGIK_PRODUCTS:
        if product["id"] == product_id:
            return product
    return None

def get_cooling_capacity_range(rack_type: str = None) -> tuple:
    """Get the min/max cooling capacity range, optionally filtered by rack type."""
    products = COLDLOGIK_PRODUCTS
    if rack_type:
        products = [p for p in products if p["rack_type"] == rack_type]
    
    if not products:
        return (0, 0)
    
    min_capacity = min(p["max_cooling_capacity"] for p in products)
    max_capacity = max(p["max_cooling_capacity"] for p in products)
    return (min_capacity, max_capacity)

def recommend_product(cooling_kw: float, rack_type: str = None, passive_preferred: bool = False) -> Dict[str, Any]:
    """
    Recommend the best product based on cooling requirements and preferences.
    
    Args:
        cooling_kw: Required cooling capacity in kW
        rack_type: Optional rack type constraint
        passive_preferred: Whether passive cooling is preferred
        
    Returns:
        Recommended product or None if no suitable product found
    """
    # Filter products by rack type if specified
    candidates = COLDLOGIK_PRODUCTS
    if rack_type:
        candidates = [p for p in candidates if p["rack_type"] == rack_type]
    
    # If passive cooling is preferred, try to find a suitable CL21 first
    if passive_preferred:
        passive_candidates = [p for p in candidates if p["series"] == "CL21" and p["max_cooling_capacity"] >= cooling_kw]
        if passive_candidates:
            # Return the smallest passive solution that meets requirements
            return min(passive_candidates, key=lambda p: p["max_cooling_capacity"])
    
    # Find all products that can handle the required cooling
    suitable_candidates = [p for p in candidates if p["max_cooling_capacity"] >= cooling_kw]
    
    if not suitable_candidates:
        # No suitable product found - recommend the highest capacity option
        return max(candidates, key=lambda p: p["max_cooling_capacity"])
    
    # Return the most appropriately sized product
    # We look for the product with capacity closest to but not less than the requirement
    return min(suitable_candidates, key=lambda p: p["max_cooling_capacity"])
