# main.py

"""
Main entry point for the Data Center Cooling Calculator.

This module implements the main calculator logic that integrates all the components,
selects appropriate models, and produces comprehensive results.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Union

from database.product_data import COLDLOGIK_PRODUCTS, recommend_product
from database.schema import DatabaseManager
from calculations.cooling_models import ActiveCoolingModel, PassiveCoolingModel, HPCCoolingModel
from utils.unit_conversion import convert_temperature, convert_power, convert_flow_rate
from utils.report_generator import generate_technical_report, generate_commercial_report
from utils.validation import validate_input_parameters
from api.app import create_api_app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("calculator.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DataCenterCoolingCalculator:
    """
    Main calculator class that integrates all components.
    
    This class provides the high-level interface for the cooling calculator,
    handling product selection, model creation, and calculation orchestration.
    """
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize the calculator.
        
        Args:
            data_dir: Directory containing data files (default: "./data")
        """
        self.data_dir = data_dir
        
        # Load fluid properties
        self.fluid_properties = {
            "water": {
                "density": 998.0,  # kg/m³
                "specific_heat": 4.182,  # kJ/kg·K
                "viscosity": 0.001,  # Pa·s
                "thermal_conductivity": 0.6  # W/m·K
            },
            "ethylene_glycol": {
                "density": 1120.0,  # kg/m³
                "specific_heat": 2.4,  # kJ/kg·K
                "viscosity": 0.016,  # Pa·s
                "thermal_conductivity": 0.25  # W/m·K
            },
            "propylene_glycol": {
                "density": 1040.0,  # kg/m³
                "specific_heat": 2.5,  # kJ/kg·K
                "viscosity": 0.04,  # Pa·s
                "thermal_conductivity": 0.2  # W/m·K
            }
        }
        
        # Initialize product database
        self.products = {product["id"]: product for product in COLDLOGIK_PRODUCTS}
        
        logger.info(f"Initialized DataCenterCoolingCalculator with {len(self.products)} products")
    
    def calculate(self, cooling_kw: float, room_temp: float, desired_temp: float, 
                 water_temp: float, **kwargs) -> Dict[str, Any]:
        """
        Perform cooling calculation based on input parameters.
        
        Args:
            cooling_kw: Required cooling capacity in kW
            room_temp: Room temperature in °C
            desired_temp: Desired room temperature in °C
            water_temp: Water supply temperature in °C
            **kwargs: Additional optional parameters:
                - product_id: Specific product ID to use
                - rack_type: Rack type (e.g., "42U600", "48U800")
                - passive_preferred: Whether to prefer passive cooling
                - fluid_type: Type of cooling fluid
                - glycol_percentage: Percentage of glycol in mixture
                - flow_rate: Water flow rate in m³/h
                - return_water_temp: Water return temperature in °C
                - fan_speed_percentage: Fan speed as percentage
                - server_air_flow: Server-provided air flow for passive cooling
                - server_pressure: Server fan pressure for passive cooling
                - units: Preferred units ('metric' or 'imperial')
                - include_commercial: Whether to include commercial calculations
                - location: Geographical location
                - operating_hours: Operating hours per year
                - electricity_cost: Electricity cost per kWh
                - carbon_factor: Carbon emissions factor in kg CO2/kWh
                
        Returns:
            Dictionary containing calculation results
        """
        # Convert units if using imperial
        if kwargs.get("units") == "imperial":
            cooling_kw = convert_power(cooling_kw, "ton", "kw")
            room_temp = convert_temperature(room_temp, "f", "c")
            desired_temp = convert_temperature(desired_temp, "f", "c")
            water_temp = convert_temperature(water_temp, "f", "c")
            
            if "flow_rate" in kwargs:
                kwargs["flow_rate"] = convert_flow_rate(kwargs["flow_rate"], "gpm", "m3h")
            
            if "return_water_temp" in kwargs:
                kwargs["return_water_temp"] = convert_temperature(kwargs["return_water_temp"], "f", "c")
        
        # Validate input parameters
        validation_result = validate_input_parameters(
            cooling_kw, room_temp, desired_temp, water_temp, **kwargs
        )
        
        if not validation_result["valid"]:
            return {"error": validation_result["message"]}
        
        # Determine which product to use
        product_id = kwargs.get("product_id")
        if product_id and product_id in self.products:
            product = self.products[product_id]
        else:
            # Select product based on cooling requirements and preferences
            product = recommend_product(
                cooling_kw, 
                kwargs.get("rack_type"),
                kwargs.get("passive_preferred", False)
            )
            
            if not product:
                return {"error": "No suitable product found for the specified requirements"}
        
        logger.info(f"Selected product: {product['name']} (ID: {product['id']})")
        
        # Determine fluid properties
        fluid_type = kwargs.get("fluid_type", "water")
        glycol_percentage = kwargs.get("glycol_percentage", 0)
        
        if fluid_type not in self.fluid_properties:
            return {"error": f"Unsupported fluid type: {fluid_type}"}
        
        # Adjust fluid properties for glycol mixture
        fluid_properties = self._adjust_fluid_properties(
            self.fluid_properties[fluid_type],
            fluid_type,
            glycol_percentage
        )
        
        # Create appropriate cooling model based on product series
        series = product.get("series", "")
        if series == "CL21":
            # Passive cooling model
            model = PassiveCoolingModel(product, fluid_properties)
        elif series == "CL23":
            # HPC cooling model
            model = HPCCoolingModel(product, fluid_properties)
        else:
            # Standard active cooling model
            model = ActiveCoolingModel(product, fluid_properties)
        
        # Perform calculation
        result = model.calculate(cooling_kw, room_temp, desired_temp, water_temp, **kwargs)
        
        # Add product information to result
        result["product"] = {
            "id": product["id"],
            "name": product["name"],
            "series": product.get("series", ""),
            "rack_type": product.get("rack_type", ""),
            "dimensions": product.get("dimensions", {}),
            "max_cooling_capacity": product.get("max_cooling_capacity", 0)
        }
        
        # Convert back to imperial units if requested
        if kwargs.get("units") == "imperial":
            result = self._convert_results_to_imperial(result)
        
        # Generate reports if requested
        if kwargs.get("generate_reports", False):
            report_dir = kwargs.get("report_dir", "./reports")
            os.makedirs(report_dir, exist_ok=True)
            
            # Generate technical report
            tech_report_path = os.path.join(report_dir, f"technical_report_{product['id']}.pdf")
            generate_technical_report(result, tech_report_path)
            result["technical_report_path"] = tech_report_path
            
            # Generate commercial report if included
            if "commercial" in result:
                comm_report_path = os.path.join(report_dir, f"commercial_report_{product['id']}.pdf")
                generate_commercial_report(result, comm_report_path)
                result["commercial_report_path"] = comm_report_path
        
        return result
    
    def recommend_products(self, cooling_kw: float, **kwargs) -> List[Dict[str, Any]]:
        """
        Recommend suitable products based on cooling requirements.
        
        Args:
            cooling_kw: Required cooling capacity in kW
            **kwargs: Additional parameters:
                - rack_type: Optional rack type constraint
                - max_results: Maximum number of recommendations to return
                - include_details: Whether to include detailed product information
                
        Returns:
            List of recommended products
        """
        # Convert units if using imperial
        if kwargs.get("units") == "imperial":
            cooling_kw = convert_power(cooling_kw, "ton", "kw")
        
        # Get constraints
        rack_type = kwargs.get("rack_type")
        max_results = kwargs.get("max_results", 3)
        include_details = kwargs.get("include_details", False)
        
        # Filter products by rack type if specified
        candidates = list(self.products.values())
        if rack_type:
            candidates = [p for p in candidates if p.get("rack_type") == rack_type]
        
        # Find products that can handle the required cooling
        suitable_products = [p for p in candidates if p.get("max_cooling_capacity", 0) >= cooling_kw]
        
        # If no suitable products, recommend products with highest capacity
        if not suitable_products:
            suitable_products = sorted(
                candidates,
                key=lambda p: p.get("max_cooling_capacity", 0),
                reverse=True
            )[:max_results]
        else:
            # Sort by appropriateness (closest capacity to requirement)
            suitable_products = sorted(
                suitable_products,
                key=lambda p: abs(p.get("max_cooling_capacity", 0) - cooling_kw)
            )[:max_results]
        
        # Prepare results
        recommendations = []
        for product in suitable_products:
            if include_details:
                # Include full product details
                recommendations.append(product)
            else:
                # Include only basic information
                recommendations.append({
                    "id": product["id"],
                    "name": product["name"],
                    "series": product.get("series", ""),
                    "rack_type": product.get("rack_type", ""),
                    "max_cooling_capacity": product.get("max_cooling_capacity", 0),
                    "dimensions": product.get("dimensions", {}),
                    "passive": product.get("series") == "CL21"
                })
        
        return recommendations
    
    def get_product_info(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Dictionary containing product information or None if not found
        """
        return self.products.get(product_id)
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Get information about all available products.
        
        Returns:
            List of all products
        """
        return list(self.products.values())
    
    def _adjust_fluid_properties(self, base_properties: Dict[str, float],
                                fluid_type: str, glycol_percentage: float) -> Dict[str, float]:
        """
        Adjust fluid properties for glycol mixtures.
        
        Args:
            base_properties: Base fluid properties
            fluid_type: Type of fluid
            glycol_percentage: Percentage of glycol (0-100)
            
        Returns:
            Adjusted fluid properties
        """
        if fluid_type == "water" or glycol_percentage == 0:
            return base_properties
        
        # Simplified adjustment factors based on glycol percentage
        # In a real implementation, this would use more detailed models
        glycol_factor = glycol_percentage / 100.0
        
        if fluid_type == "ethylene_glycol":
            return {
                "density": base_properties["density"] * (1 + 0.13 * glycol_factor),
                "specific_heat": base_properties["specific_heat"] * (1 - 0.45 * glycol_factor),
                "viscosity": base_properties["viscosity"] * (1 + 10 * glycol_factor),
                "thermal_conductivity": base_properties["thermal_conductivity"] * (1 - 0.3 * glycol_factor)
            }
        elif fluid_type == "propylene_glycol":
            return {
                "density": base_properties["density"] * (1 + 0.06 * glycol_factor),
                "specific_heat": base_properties["specific_heat"] * (1 - 0.4 * glycol_factor),
                "viscosity": base_properties["viscosity"] * (1 + 15 * glycol_factor),
                "thermal_conductivity": base_properties["thermal_conductivity"] * (1 - 0.35 * glycol_factor)
            }
        
        return base_properties
    
    def _convert_results_to_imperial(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert calculation results from metric to imperial units.
        
        Args:
            results: Calculation results in metric units
            
        Returns:
            Calculation results in imperial units
        """
        # Create a deep copy of results to avoid modifying the original
        import copy
        imperial_results = copy.deepcopy(results)
        
        # Convert cooling capacity: kW to tons
        if "cooling_capacity" in imperial_results:
            imperial_results["cooling_capacity"] = convert_power(
                imperial_results["cooling_capacity"], "kw", "ton"
            )
        
        # Convert water-side parameters
        if "water_side" in imperial_results:
            water_side = imperial_results["water_side"]
            
            # Convert flow rate: m³/h to GPM
            if "flow_rate" in water_side:
                water_side["flow_rate"] = convert_flow_rate(
                    water_side["flow_rate"], "m3h", "gpm"
                )
                water_side["flow_rate_unit"] = "GPM"
            
            # Convert temperatures: °C to °F
            for key in ["supply_temp", "return_temp"]:
                if key in water_side:
                    water_side[key] = convert_temperature(
                        water_side[key], "c", "f"
                    )
            
            # Convert pressure: kPa to PSI
            if "pressure_drop" in water_side:
                water_side["pressure_drop"] = water_side["pressure_drop"] * 0.145038
                water_side["pressure_drop_unit"] = "PSI"
        
        # Convert air-side parameters
        if "air_side" in imperial_results:
            air_side = imperial_results["air_side"]
            
            # Convert air flow: m³/h to CFM
            for key in ["required_air_flow", "actual_air_flow", "min_air_flow", "max_air_flow"]:
                if key in air_side:
                    air_side[key] = air_side[key] * 0.589
                    if key + "_unit" not in air_side:
                        air_side[key + "_unit"] = "CFM"
            
            # Convert pressure: Pa to inWC
            for key in ["static_pressure", "door_pressure_drop", "server_pressure"]:
                if key in air_side:
                    air_side[key] = air_side[key] * 0.00401463
                    if key + "_unit" not in air_side:
                        air_side[key + "_unit"] = "inWC"
                        
            # Convert actual cooling capacity if present
            if "actual_cooling_capacity" in air_side:
                air_side["actual_cooling_capacity"] = convert_power(
                    air_side["actual_cooling_capacity"], "kw", "ton"
                )
        
        # Convert valve data
        if "valve_recommendation" in imperial_results:
            valve = imperial_results["valve_recommendation"]
            
            if "max_flow_rate" in valve:
                valve["max_flow_rate"] = convert_flow_rate(
                    valve["max_flow_rate"], "m3h", "gpm"
                )
                valve["max_flow_rate_unit"] = "GPM"
        
        # Convert product dimensions
        if "product" in imperial_results and "dimensions" in imperial_results["product"]:
            dims = imperial_results["product"]["dimensions"]
            
            for key in ["height", "width", "depth"]:
                if key in dims:
                    dims[key] = dims[key] * 0.0393701  # mm to inches
                    if key + "_unit" not in dims:
                        dims[key + "_unit"] = "in"
            
            if "wet_weight" in dims:
                dims["wet_weight"] = dims["wet_weight"] * 2.20462  # kg to lbs
                dims["wet_weight_unit"] = "lbs"
        
        return imperial_results


def create_calculator():
    """Create and initialize a calculator instance."""
    return DataCenterCoolingCalculator()


def main():
    """Main entry point when running as a script."""
    # Parse command-line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Center Cooling Calculator")
    parser.add_argument("--cooling_kw", type=float, required=True,
                       help="Required cooling capacity in kW")
    parser.add_argument("--room_temp", type=float, required=True,
                       help="Room temperature in °C")
    parser.add_argument("--desired_temp", type=float, required=True,
                       help="Desired room temperature in °C")
    parser.add_argument("--water_temp", type=float, required=True,
                       help="Water supply temperature in °C")
    parser.add_argument("--product_id", type=str,
                       help="Specific product ID to use")
    parser.add_argument("--rack_type", type=str,
                       help="Rack type (e.g., '42U600', '48U800')")
    parser.add_argument("--passive", action="store_true",
                       help="Prefer passive cooling if available")
    parser.add_argument("--fluid_type", type=str, default="water",
                       help="Type of cooling fluid (water, ethylene_glycol, propylene_glycol)")
    parser.add_argument("--glycol_percentage", type=float, default=0,
                       help="Percentage of glycol in mixture (0-100)")
    parser.add_argument("--flow_rate", type=float,
                       help="Water flow rate in m³/h")
    parser.add_argument("--return_water_temp", type=float,
                       help="Water return temperature in °C")
    parser.add_argument("--fan_speed", type=float,
                       help="Fan speed as percentage (0-100)")
    parser.add_argument("--units", type=str, default="metric",
                       help="Preferred units (metric or imperial)")
    parser.add_argument("--commercial", action="store_true",
                       help="Include commercial calculations")
    parser.add_argument("--output", type=str,
                       help="Output file for results (JSON format)")
    
    args = parser.parse_args()
    
    # Create calculator
    calculator = create_calculator()
    
    # Prepare parameters
    params = {
        "cooling_kw": args.cooling_kw,
        "room_temp": args.room_temp,
        "desired_temp": args.desired_temp,
        "water_temp": args.water_temp,
        "product_id": args.product_id,
        "rack_type": args.rack_type,
        "passive_preferred": args.passive,
        "fluid_type": args.fluid_type,
        "glycol_percentage": args.glycol_percentage,
        "units": args.units,
        "include_commercial": args.commercial
    }
    
    if args.flow_rate is not None:
        params["flow_rate"] = args.flow_rate
    
    if args.return_water_temp is not None:
        params["return_water_temp"] = args.return_water_temp
    
    if args.fan_speed is not None:
        params["fan_speed_percentage"] = args.fan_speed
    
    # Perform calculation
    result = calculator.calculate(**params)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))


def start_api(host="0.0.0.0", port=5000, debug=False):
    """Start the API server."""
    app = create_api_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
