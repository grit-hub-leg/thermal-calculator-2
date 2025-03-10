# calculations/cooling_models.py

import math
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from .thermal import heat_transfer_rate, log_mean_temp_difference, effectiveness_ntu_method
from .fluid_dynamics import reynolds_number, darcy_friction_factor, pressure_drop_pipe
from .efficiency import coefficient_of_performance, energy_efficiency_ratio, power_usage_effectiveness

logger = logging.getLogger(__name__)

class BaseCoolingModel:
    """Base class for all cooling models."""
    
    def __init__(self, product_data: Dict[str, Any], fluid_properties: Dict[str, Any]):
        self.product = product_data
        self.fluid_properties = fluid_properties
        self.results = {}
    
    def calculate(self, cooling_kw: float, room_temp: float, desired_temp: float, 
                 water_temp: float, **kwargs) -> Dict[str, Any]:
        """Abstract method to calculate cooling performance."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def validate_input_parameters(self, cooling_kw: float, room_temp: float, 
                                 desired_temp: float, water_temp: float) -> Tuple[bool, str]:
        """
        Validate input parameters against product constraints.
        
        Returns:
            Tuple containing (valid: bool, message: str)
        """
        # Check if cooling capacity is within product limits
        if cooling_kw > self.product["max_cooling_capacity"]:
            return (False, f"Cooling requirement ({cooling_kw} kW) exceeds maximum capacity "
                          f"({self.product['max_cooling_capacity']} kW)")
        
        # Check if water temperature is within allowable range
        water_specs = self.product.get("water_specs", {})
        min_water_temp = water_specs.get("min_inlet_temp", 0)
        max_water_temp = water_specs.get("max_inlet_temp", 100)
        
        if water_temp < min_water_temp:
            return (False, f"Water temperature ({water_temp}°C) is below minimum "
                          f"({min_water_temp}°C)")
            
        if water_temp > max_water_temp:
            return (False, f"Water temperature ({water_temp}°C) is above maximum "
                          f"({max_water_temp}°C)")
            
        # Additional validations can be added as needed
        return (True, "All parameters valid")

    def _calculate_water_flow_rate(self, cooling_kw: float, water_temp: float, 
                                  delta_t: float = 5.0) -> float:
        """
        Calculate required water flow rate based on cooling load.
        
        Args:
            cooling_kw: Cooling capacity in kW
            water_temp: Water inlet temperature in °C
            delta_t: Temperature difference between inlet and outlet in °C
            
        Returns:
            Required water flow rate in m³/h
        """
        # Get fluid properties
        density = self.fluid_properties.get("density", 998.0)  # kg/m³
        specific_heat = self.fluid_properties.get("specific_heat", 4.182)  # kJ/kg·K
        
        # Calculate mass flow rate (kg/s)
        # Q = ṁ × cp × ΔT
        # ṁ = Q / (cp × ΔT)
        mass_flow_rate = cooling_kw / (specific_heat * delta_t)
        
        # Convert to volume flow rate (m³/h)
        # ṁ = ρ × V̇
        # V̇ = ṁ / ρ
        volume_flow_rate = (mass_flow_rate / density) * 3600
        
        return volume_flow_rate
    
    def _calculate_effectiveness(self, cooling_kw: float, air_flow: float, water_flow: float,
                                room_temp: float, desired_temp: float, water_temp: float) -> float:
        """
        Calculate heat exchanger effectiveness.
        
        Args:
            cooling_kw: Cooling capacity in kW
            air_flow: Air flow rate in m³/h
            water_flow: Water flow rate in m³/h
            room_temp: Room temperature in °C
            desired_temp: Desired room temperature in °C
            water_temp: Water inlet temperature in °C
            
        Returns:
            Heat exchanger effectiveness (0-1)
        """
        # Calculate capacity rates
        # Air properties
        air_density = 1.2  # kg/m³ at 20°C
        air_specific_heat = 1.005  # kJ/kg·K
        
        # Water properties
        water_density = self.fluid_properties.get("density", 998.0)  # kg/m³
        water_specific_heat = self.fluid_properties.get("specific_heat", 4.182)  # kJ/kg·K
        
        # Convert flow rates to kg/s
        air_mass_flow = (air_flow * air_density) / 3600
        water_mass_flow = (water_flow * water_density) / 3600
        
        # Calculate capacity rates (W/K)
        air_capacity_rate = air_mass_flow * air_specific_heat * 1000
        water_capacity_rate = water_mass_flow * water_specific_heat * 1000
        
        # Determine C_min and C_max
        c_min = min(air_capacity_rate, water_capacity_rate)
        c_max = max(air_capacity_rate, water_capacity_rate)
        
        # Calculate capacity ratio
        c_ratio = c_min / c_max if c_max > 0 else 0
        
        # Calculate maximum possible heat transfer
        temp_diff = room_temp - water_temp
        q_max = c_min * temp_diff
        
        # Calculate actual heat transfer
        q_actual = cooling_kw * 1000  # W
        
        # Calculate effectiveness
        effectiveness = q_actual / q_max if q_max > 0 else 0
        
        return min(1.0, max(0.0, effectiveness))  # Ensure between 0 and 1
    
    def recommend_valve(self, flow_rate: float) -> Dict[str, Any]:
        """
        Recommend appropriate valve based on flow rate.
        
        Args:
            flow_rate: Required flow rate in m³/h
            
        Returns:
            Dictionary containing valve recommendation
        """
        # Get valve options
        valve_options = self.product.get("valve_options", [])
        
        if not valve_options:
            return {
                "error": "No valve options available for this product",
                "valve_type": None,
                "valve_size": None
            }
        
        # Sort by max flow rate
        sorted_valves = sorted(valve_options, key=lambda v: v["max_flow_rate"])
        
        # Find smallest valve that can handle the flow rate
        selected_valve = None
        for valve in sorted_valves:
            if flow_rate <= valve["max_flow_rate"]:
                selected_valve = valve
                break
        
        # If no valve can handle the flow rate, recommend the largest available
        if selected_valve is None:
            selected_valve = sorted_valves[-1]
            sufficient = False
        else:
            sufficient = True
        
        # Calculate valve utilization percentage
        utilization = (flow_rate / selected_valve["max_flow_rate"]) * 100 if selected_valve["max_flow_rate"] > 0 else 0
        
        # Calculate recommended valve settings (40-80% range as mentioned in transcript)
        nominal_setting = utilization
        min_setting = max(0, nominal_setting - 20)
        max_setting = min(100, nominal_setting + 20)
        
        return {
            "valve_type": selected_valve["type"],
            "valve_size": selected_valve["size"],
            "max_flow_rate": selected_valve["max_flow_rate"],
            "kv_value": selected_valve["kv_value"],
            "sufficient": sufficient,
            "utilization_percentage": utilization,
            "recommended_settings": {
                "nominal": nominal_setting,
                "min": min_setting,
                "max": max_setting
            }
        }
    
    def calculate_energy_costs(self, power_consumption: float, operating_hours: float, 
                              electricity_cost: float) -> Dict[str, float]:
        """
        Calculate energy costs.
        
        Args:
            power_consumption: Power consumption in W
            operating_hours: Operating hours per year
            electricity_cost: Electricity cost per kWh
            
        Returns:
            Dictionary containing cost calculations
        """
        # Convert power to kW
        power_kw = power_consumption / 1000
        
        # Calculate annual energy consumption (kWh)
        annual_energy = power_kw * operating_hours
        
        # Calculate annual cost
        annual_cost = annual_energy * electricity_cost
        
        return {
            "power_kw": power_kw,
            "annual_energy_kwh": annual_energy,
            "annual_cost": annual_cost
        }
    
    def calculate_environmental_impact(self, annual_energy: float, 
                                      carbon_factor: float) -> Dict[str, float]:
        """
        Calculate environmental impact metrics.
        
        Args:
            annual_energy: Annual energy consumption in kWh
            carbon_factor: Carbon emissions factor in kg CO2/kWh
            
        Returns:
            Dictionary containing environmental impact metrics
        """
        # Calculate annual carbon emissions
        annual_carbon = annual_energy * carbon_factor
        
        # Convert to equivalent metrics (trees, cars) as mentioned in transcript
        tree_equivalent = annual_carbon * 0.039  # Trees needed to absorb carbon
        car_equivalent = annual_carbon / 4600  # Cars removed for a year
        
        return {
            "annual_carbon_kg": annual_carbon,
            "tree_equivalent": tree_equivalent,
            "car_equivalent": car_equivalent
        }


class ActiveCoolingModel(BaseCoolingModel):
    """
    Cooling model for active rear door heat exchangers (CL20, CL23 series).
    
    These models have fans that actively move air through the heat exchanger.
    """
    
    def calculate(self, cooling_kw: float, room_temp: float, desired_temp: float, 
                 water_temp: float, **kwargs) -> Dict[str, Any]:
        """
        Calculate cooling performance for active rear door heat exchangers.
        
        Args:
            cooling_kw: Required cooling capacity in kW
            room_temp: Room inlet temperature in °C
            desired_temp: Desired room outlet temperature in °C
            water_temp: Water inlet temperature in °C
            **kwargs: Additional parameters including:
                - flow_rate: Water flow rate in m³/h (if None, will be calculated)
                - return_water_temp: Water return temperature in °C (if None, will be calculated)
                - fan_speed_percentage: Fan speed as percentage (if None, will be calculated)
                
        Returns:
            Dictionary containing calculation results
        """
        # Validate input parameters
        valid, message = self.validate_input_parameters(cooling_kw, room_temp, desired_temp, water_temp)
        if not valid:
            return {"error": message}
        
        # Extract additional parameters
        flow_rate = kwargs.get("flow_rate")
        return_water_temp = kwargs.get("return_water_temp")
        fan_speed_percentage = kwargs.get("fan_speed_percentage")
        
        # Water-side calculations
        water_side = self._calculate_water_side(cooling_kw, water_temp, return_water_temp, flow_rate)
        
        # Air-side calculations
        air_side = self._calculate_air_side(cooling_kw, room_temp, desired_temp, fan_speed_percentage)
        
        # Valve recommendation
        valve_recommendation = self.recommend_valve(water_side["flow_rate"])
        
        # Calculate efficiency metrics
        efficiency = self._calculate_efficiency_metrics(cooling_kw, air_side["power_consumption"])
        
        # Compute commercial metrics if requested
        commercial = None
        if kwargs.get("include_commercial", True):
            commercial = self._calculate_commercial_metrics(
                cooling_kw, 
                air_side["power_consumption"],
                kwargs.get("operating_hours", 8760),
                kwargs.get("electricity_cost", 0.15),
                kwargs.get("carbon_factor", 0.5)
            )
        
        # Combine results
        self.results = {
            "cooling_capacity": cooling_kw,
            "water_side": water_side,
            "air_side": air_side,
            "valve_recommendation": valve_recommendation,
            "efficiency": efficiency
        }
        
        if commercial:
            self.results["commercial"] = commercial
            
        return self.results
    
    def _calculate_water_side(self, cooling_kw: float, water_temp: float, 
                             return_water_temp: Optional[float] = None,
                             flow_rate: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate water-side parameters.
        
        Args:
            cooling_kw: Cooling capacity in kW
            water_temp: Water inlet temperature in °C
            return_water_temp: Water return temperature in °C (optional)
            flow_rate: Water flow rate in m³/h (optional)
            
        Returns:
            Dictionary containing water-side calculations
        """
        # Get water specifications
        water_specs = self.product.get("water_specs", {})
        
        # We need either return_water_temp or flow_rate
        if return_water_temp is None and flow_rate is None:
            # Use nominal delta T from product specs or default to 5°C
            delta_t = water_specs.get("nominal_delta_t", 5.0)
            return_water_temp = water_temp + delta_t
        
        # Calculate the missing parameter
        if flow_rate is None:
            # Calculate flow rate based on cooling capacity and temperatures
            delta_t = return_water_temp - water_temp
            flow_rate = self._calculate_water_flow_rate(cooling_kw, water_temp, delta_t)
        elif return_water_temp is None:
            # Calculate return temperature based on cooling capacity and flow rate
            # Q = ṁ × cp × ΔT
            # ΔT = Q / (ṁ × cp)
            density = self.fluid_properties.get("density", 998.0)  # kg/m³
            specific_heat = self.fluid_properties.get("specific_heat", 4.182)  # kJ/kg·K
            
            # Convert flow rate to kg/s
            mass_flow_rate = (flow_rate * density) / 3600
            
            # Calculate temperature difference
            delta_t = cooling_kw / (mass_flow_rate * specific_heat)
            
            # Calculate return temperature
            return_water_temp = water_temp + delta_t
        
        # Calculate pressure drop
        pressure_drop = self._calculate_water_pressure_drop(flow_rate)
        
        return {
            "flow_rate": flow_rate,
            "supply_temp": water_temp,
            "return_temp": return_water_temp,
            "delta_t": return_water_temp - water_temp,
            "pressure_drop": pressure_drop
        }
    
    def _calculate_water_pressure_drop(self, flow_rate: float) -> float:
        """
        Calculate water-side pressure drop.
        
        Args:
            flow_rate: Water flow rate in m³/h
            
        Returns:
            Pressure drop in kPa
        """
        # Get coil geometry
        coil = self.product.get("coil_geometry", {})
        
        # Simple pressure drop calculation
        # In a real implementation, this would be more detailed
        tube_diameter = coil.get("tube_diameter", 12.0) / 1000  # mm to m
        tube_length = coil.get("tube_length", 1.0)  # m
        number_of_passes = coil.get("number_of_passes", 4)
        
        # Calculate flow velocity
        pipe_area = math.pi * (tube_diameter / 2) ** 2
        velocity = (flow_rate / 3600) / pipe_area  # m/s
        
        # Get fluid properties
        density = self.fluid_properties.get("density", 998.0)  # kg/m³
        viscosity = self.fluid_properties.get("viscosity", 0.001)  # Pa·s
        
        # Calculate Reynolds number
        re = reynolds_number(velocity, tube_diameter, density, viscosity)
        
        # Calculate friction factor
        relative_roughness = 0.0002 / tube_diameter  # Assumed pipe roughness of 0.0002 m
        f = darcy_friction_factor(re, relative_roughness)
        
        # Calculate pressure drop
        pdrop = pressure_drop_pipe(f, tube_length * number_of_passes, tube_diameter, density, velocity)
        
        # Convert to kPa
        return pdrop / 1000
    
    def _calculate_air_side(self, cooling_kw: float, room_temp: float, 
                           desired_temp: float, 
                           fan_speed_percentage: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate air-side parameters.
        
        Args:
            cooling_kw: Cooling capacity in kW
            room_temp: Room temperature in °C
            desired_temp: Desired temperature in °C
            fan_speed_percentage: Fan speed percentage (optional)
            
        Returns:
            Dictionary containing air-side calculations
        """
        # Get fan specifications
        fan_specs = self.product.get("fan_specs", {})
        num_fans = self.product.get("number_of_fans", 1)
        
        # Calculate required air flow
        # Q = ṁ × cp × ΔT
        # ṁ = Q / (cp × ΔT)
        air_density = 1.2  # kg/m³
        air_specific_heat = 1.005  # kJ/kg·K
        
        delta_t = room_temp - desired_temp
        
        # Convert cooling capacity to W
        cooling_w = cooling_kw * 1000
        
        # Calculate required air mass flow rate
        air_mass_flow = cooling_w / (air_specific_heat * 1000 * delta_t)
        
        # Convert to volumetric flow rate in m³/h
        required_air_flow = (air_mass_flow / air_density) * 3600
        
        # Calculate static pressure based on flow rate
        # This is a simplified model
        static_pressure = 25.0 + 0.05 * (required_air_flow / 1000) ** 2
        
        # Calculate required fan speed if not provided
        if fan_speed_percentage is None:
            # Get nominal air flow
            nominal_air_flow = fan_specs.get("nominal_air_flow", 3000.0) * num_fans
            
            # Calculate fan speed percentage
            fan_speed_percentage = (required_air_flow / nominal_air_flow) * 100
            
            # Ensure fan speed is within limits
            fan_speed_percentage = min(100.0, max(0.0, fan_speed_percentage))
        
        # Calculate actual air flow based on fan speed
        actual_air_flow = (fan_specs.get("nominal_air_flow", 3000.0) * num_fans * fan_speed_percentage) / 100
        
        # Calculate power consumption using fan laws
        # P2/P1 = (n2/n1)³
        nominal_power = fan_specs.get("nominal_power", 50.0)  # W per fan
        power_ratio = (fan_speed_percentage / 100) ** 3
        power_consumption = nominal_power * power_ratio * num_fans
        
        # Calculate noise level
        # Noise increases by approximately 15*log10(n2/n1) dB
        nominal_noise = fan_specs.get("nominal_noise", 55.0)  # dB(A)
        noise_increase = 15 * math.log10(fan_speed_percentage / 100) if fan_speed_percentage > 0 else 0
        noise_level = nominal_noise + noise_increase if fan_speed_percentage > 0 else 0
        
        # Check if fans meet the requirements
        max_air_flow = fan_specs.get("max_air_flow", 4000.0) * num_fans
        fan_sufficient = required_air_flow <= max_air_flow
        
        return {
            "required_air_flow": required_air_flow,
            "actual_air_flow": actual_air_flow,
            "static_pressure": static_pressure,
            "fan_speed_percentage": fan_speed_percentage,
            "power_consumption": power_consumption,
            "noise_level": noise_level,
            "number_of_fans": num_fans,
            "fan_sufficient": fan_sufficient
        }
    
    def _calculate_efficiency_metrics(self, cooling_kw: float, power_consumption: float) -> Dict[str, float]:
        """
        Calculate efficiency metrics.
        
        Args:
            cooling_kw: Cooling capacity in kW
            power_consumption: Power consumption in W
            
        Returns:
            Dictionary containing efficiency metrics
        """
        # Get efficiency specifications
        efficiency_specs = self.product.get("efficiency", {})
        
        # Convert power to kW
        power_kw = power_consumption / 1000
        
        # Calculate COP (Coefficient of Performance)
        cop = cooling_kw / power_kw if power_kw > 0 else float('inf')
        
        # Calculate EER (Energy Efficiency Ratio)
        # EER = cooling capacity (BTU/h) / power input (W)
        # 1 kW = 3412 BTU/h
        eer = (cooling_kw * 3412) / power_consumption if power_consumption > 0 else float('inf')
        
        # Get product PUE improvement
        min_pue = efficiency_specs.get("min_pue", 1.2)
        
        # Calculate actual PUE based on current operating conditions
        # PUE = (IT Load + Cooling Power) / IT Load
        # Assuming cooling_kw represents IT load
        actual_pue = (cooling_kw + power_kw) / cooling_kw if cooling_kw > 0 else float('inf')
        
        return {
            "cop": cop,
            "eer": eer,
            "product_min_pue": min_pue,
            "actual_pue": actual_pue,
            "power_usage": power_kw
        }
    
    def _calculate_commercial_metrics(self, cooling_kw: float, power_consumption: float,
                                     operating_hours: float, electricity_cost: float,
                                     carbon_factor: float) -> Dict[str, Any]:
        """
        Calculate commercial metrics.
        
        Args:
            cooling_kw: Cooling capacity in kW
            power_consumption: Power consumption in W
            operating_hours: Operating hours per year
            electricity_cost: Electricity cost per kWh
            carbon_factor: Carbon emissions factor in kg CO2/kWh
            
        Returns:
            Dictionary containing commercial metrics
        """
        # Calculate energy costs
        energy_costs = self.calculate_energy_costs(
            power_consumption, operating_hours, electricity_cost
        )
        
        # Calculate environmental impact
        environmental = self.calculate_environmental_impact(
            energy_costs["annual_energy_kwh"], carbon_factor
        )
        
        # Calculate operational savings compared to traditional cooling
        efficiency_specs = self.product.get("efficiency", {})
        operational_savings = efficiency_specs.get("operational_savings", 0.5)  # Default 50%
        
        # Estimate traditional cooling energy consumption and costs
        traditional_power = power_consumption / (1 - operational_savings) if operational_savings < 1 else power_consumption * 10
        traditional_energy_costs = self.calculate_energy_costs(
            traditional_power, operating_hours, electricity_cost
        )
        
        # Calculate savings
        annual_savings = traditional_energy_costs["annual_cost"] - energy_costs["annual_cost"]
        
        # Estimate capital costs
        capital_cost = self._estimate_capital_cost(cooling_kw)
        
        # Calculate ROI and payback period
        roi = (annual_savings / capital_cost) * 100 if capital_cost > 0 else float('inf')
        payback_years = capital_cost / annual_savings if annual_savings > 0 else float('inf')
        
        return {
            "energy_costs": energy_costs,
            "environmental": environmental,
            "traditional_energy_costs": traditional_energy_costs,
            "annual_savings": annual_savings,
            "capital_cost": capital_cost,
            "roi_percentage": roi,
            "payback_years": payback_years
        }
    
    def _estimate_capital_cost(self, cooling_kw: float) -> float:
        """
        Estimate capital cost of the cooling system.
        
        Args:
            cooling_kw: Cooling capacity in kW
            
        Returns:
            Estimated capital cost
        """
        # This is a simplified model
        # In a real implementation, this would be based on actual pricing data
        base_cost = 10000  # Base cost for any CL series product
        per_kw_cost = 500  # Cost per kW of cooling capacity
        
        return base_cost + (per_kw_cost * cooling_kw)


class PassiveCoolingModel(BaseCoolingModel):
    """
    Cooling model for passive rear door heat exchangers (CL21 series).
    
    These models have no fans and rely on server fans to move air through the heat exchanger.
    """
    
    def calculate(self, cooling_kw: float, room_temp: float, desired_temp: float, 
                 water_temp: float, **kwargs) -> Dict[str, Any]:
        """
        Calculate cooling performance for passive rear door heat exchangers.
        
        Args:
            cooling_kw: Required cooling capacity in kW
            room_temp: Room inlet temperature in °C
            desired_temp: Desired room outlet temperature in °C
            water_temp: Water inlet temperature in °C
            **kwargs: Additional parameters including:
                - flow_rate: Water flow rate in m³/h (if None, will be calculated)
                - return_water_temp: Water return temperature in °C (if None, will be calculated)
                - server_air_flow: Server-provided air flow in m³/h
                - server_pressure: Server fan pressure in Pa
                
        Returns:
            Dictionary containing calculation results
        """
        # Validate input parameters
        valid, message = self.validate_input_parameters(cooling_kw, room_temp, desired_temp, water_temp)
        if not valid:
            return {"error": message}
        
        # Extract additional parameters
        flow_rate = kwargs.get("flow_rate")
        return_water_temp = kwargs.get("return_water_temp")
        server_air_flow = kwargs.get("server_air_flow")
        server_pressure = kwargs.get("server_pressure", 20.0)  # Default 20 Pa as in specs
        
        # Water-side calculations
        water_side = self._calculate_water_side(cooling_kw, water_temp, return_water_temp, flow_rate)
        
        # Air-side calculations
        air_side = self._calculate_passive_air_side(cooling_kw, room_temp, desired_temp, server_air_flow, server_pressure)
        
        # Valve recommendation
        valve_recommendation = self.recommend_valve(water_side["flow_rate"])
        
        # Calculate efficiency metrics
        efficiency = self._calculate_passive_efficiency_metrics(cooling_kw)
        
        # Compute commercial metrics if requested
        commercial = None
        if kwargs.get("include_commercial", True):
            commercial = self._calculate_passive_commercial_metrics(
                cooling_kw,
                kwargs.get("operating_hours", 8760),
                kwargs.get("electricity_cost", 0.15),
                kwargs.get("carbon_factor", 0.5)
            )
        
        # Combine results
        self.results = {
            "cooling_capacity": cooling_kw,
            "water_side": water_side,
            "air_side": air_side,
            "valve_recommendation": valve_recommendation,
            "efficiency": efficiency
        }
        
        if commercial:
            self.results["commercial"] = commercial
            
        return self.results
    
    def _calculate_water_side(self, cooling_kw: float, water_temp: float, 
                             return_water_temp: Optional[float] = None,
                             flow_rate: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate water-side parameters for passive cooling.
        
        Identical to active cooling calculation.
        """
        # Use the same implementation as ActiveCoolingModel
        # Get water specifications
        water_specs = self.product.get("water_specs", {})
        
        # We need either return_water_temp or flow_rate
        if return_water_temp is None and flow_rate is None:
            # Use nominal delta T from product specs or default to 6°C for passive
            delta_t = water_specs.get("nominal_delta_t", 6.0)
            return_water_temp = water_temp + delta_t
        
        # Calculate the missing parameter
        if flow_rate is None:
            # Calculate flow rate based on cooling capacity and temperatures
            delta_t = return_water_temp - water_temp
            flow_rate = self._calculate_water_flow_rate(cooling_kw, water_temp, delta_t)
        elif return_water_temp is None:
            # Calculate return temperature based on cooling capacity and flow rate
            # Q = ṁ × cp × ΔT
            # ΔT = Q / (ṁ × cp)
            density = self.fluid_properties.get("density", 998.0)  # kg/m³
            specific_heat = self.fluid_properties.get("specific_heat", 4.182)  # kJ/kg·K
            
            # Convert flow rate to kg/s
            mass_flow_rate = (flow_rate * density) / 3600
            
            # Calculate temperature difference
            delta_t = cooling_kw / (mass_flow_rate * specific_heat)
            
            # Calculate return temperature
            return_water_temp = water_temp + delta_t
        
        # Calculate pressure drop
        pressure_drop = self._calculate_water_pressure_drop(flow_rate)
        
        return {
            "flow_rate": flow_rate,
            "supply_temp": water_temp,
            "return_temp": return_water_temp,
            "delta_t": return_water_temp - water_temp,
            "pressure_drop": pressure_drop
        }
    
    def _calculate_water_pressure_drop(self, flow_rate: float) -> float:
        """
        Calculate water-side pressure drop for passive cooling.
        
        Identical to active cooling calculation.
        """
        # Implementation from ActiveCoolingModel
        # Get coil geometry
        coil = self.product.get("coil_geometry", {})
        
        # Simple pressure drop calculation
        # In a real implementation, this would be more detailed
        tube_diameter = coil.get("tube_diameter", 12.0) / 1000  # mm to m
        tube_length = coil.get("tube_length", 1.0)  # m
        number_of_passes = coil.get("number_of_passes", 6)  # Usually more passes in passive
        
        # Calculate flow velocity
        pipe_area = math.pi * (tube_diameter / 2) ** 2
        velocity = (flow_rate / 3600) / pipe_area  # m/s
        
        # Get fluid properties
        density = self.fluid_properties.get("density", 998.0)  # kg/m³
        viscosity = self.fluid_properties.get("viscosity", 0.001)  # Pa·s
        
        # Calculate Reynolds number
        re = reynolds_number(velocity, tube_diameter, density, viscosity)
        
        # Calculate friction factor
        relative_roughness = 0.0002 / tube_diameter  # Assumed pipe roughness of 0.0002 m
        f = darcy_friction_factor(re, relative_roughness)
        
        # Calculate pressure drop
        pdrop = pressure_drop_pipe(f, tube_length * number_of_passes, tube_diameter, density, velocity)
        
        # Convert to kPa
        return pdrop / 1000
    
    def _calculate_passive_air_side(self, cooling_kw: float, room_temp: float, 
                                    desired_temp: float, server_air_flow: Optional[float] = None,
                                    server_pressure: float = 20.0) -> Dict[str, Any]:
        """
        Calculate air-side parameters for passive cooling.
        
        Args:
            cooling_kw: Cooling capacity in kW
            room_temp: Room temperature in °C
            desired_temp: Desired temperature in °C
            server_air_flow: Server-provided air flow in m³/h (optional)
            server_pressure: Server fan pressure in Pa (default: 20 Pa)
            
        Returns:
            Dictionary containing air-side calculations
        """
        # Get passive specifications
        passive_specs = self.product.get("passive_specs", {})
        
        # Calculate required air flow if not provided
        if server_air_flow is None:
            # Q = ṁ × cp × ΔT
            # ṁ = Q / (cp × ΔT)
            air_density = 1.2  # kg/m³
            air_specific_heat = 1.005  # kJ/kg·K
            
            delta_t = room_temp - desired_temp
            
            # Convert cooling capacity to W
            cooling_w = cooling_kw * 1000
            
            # Calculate required air mass flow rate
            air_mass_flow = cooling_w / (air_specific_heat * 1000 * delta_t)
            
            # Convert to volumetric flow rate in m³/h
            server_air_flow = (air_mass_flow / air_density) * 3600
        
        # Check if air flow is within passive system limits
        min_air_flow = passive_specs.get("min_air_flow", 1000.0)
        max_air_flow = passive_specs.get("max_air_flow", 6000.0)
        
        if server_air_flow < min_air_flow:
            air_flow_sufficient = False
            actual_cooling_capacity = (server_air_flow / min_air_flow) * cooling_kw
            warning = f"Server air flow ({server_air_flow:.1f} m³/h) is below minimum required ({min_air_flow:.1f} m³/h)"
        elif server_air_flow > max_air_flow:
            air_flow_sufficient = False
            actual_cooling_capacity = cooling_kw  # We can still achieve full cooling, but with increased pressure drop
            warning = f"Server air flow ({server_air_flow:.1f} m³/h) exceeds maximum recommended ({max_air_flow:.1f} m³/h)"
        else:
            air_flow_sufficient = True
            actual_cooling_capacity = cooling_kw
            warning = None
        
        # Calculate pressure drop through passive door
        # Higher air flow means higher pressure drop
        # This is a simplified model
        # In a real implementation, this would be based on actual test data
        base_pressure_drop = 20.0  # Pa at reference flow
        reference_flow = 3000.0  # m³/h
        
        # Pressure drop scales with square of flow rate
        pressure_drop = base_pressure_drop * (server_air_flow / reference_flow) ** 2
        
        # Check if server pressure is sufficient
        pressure_sufficient = server_pressure >= pressure_drop
        
        if not pressure_sufficient:
            # Adjust actual cooling capacity based on available pressure
            pressure_ratio = server_pressure / pressure_drop
            actual_cooling_capacity = actual_cooling_capacity * pressure_ratio
            
            if warning:
                warning += f" and server pressure ({server_pressure:.1f} Pa) is insufficient for required pressure drop ({pressure_drop:.1f} Pa)"
            else:
                warning = f"Server pressure ({server_pressure:.1f} Pa) is insufficient for required pressure drop ({pressure_drop:.1f} Pa)"
        
        return {
            "required_air_flow": server_air_flow,
            "min_air_flow": min_air_flow,
            "max_air_flow": max_air_flow,
            "air_flow_sufficient": air_flow_sufficient,
            "server_pressure": server_pressure,
            "door_pressure_drop": pressure_drop,
            "pressure_sufficient": pressure_sufficient,
            "actual_cooling_capacity": actual_cooling_capacity,
            "power_consumption": 0.0,  # Passive system has zero power consumption
            "noise_level": 0.0,  # Passive system has no fan noise
            "warning": warning
        }
    
    def _calculate_passive_efficiency_metrics(self, cooling_kw: float) -> Dict[str, float]:
        """
        Calculate efficiency metrics for passive cooling.
        
        Args:
            cooling_kw: Cooling capacity in kW
            
        Returns:
            Dictionary containing efficiency metrics
        """
        # Get efficiency specifications
        efficiency_specs = self.product.get("efficiency", {})
        
        # Passive systems have infinite COP and EER (zero energy consumption)
        cop = float('inf')
        eer = float('inf')
        
        # Get product PUE improvement
        min_pue = efficiency_specs.get("min_pue", 1.01)  # Extremely efficient
        
        # Passive cooling has zero cooling power, so PUE is ideal
        actual_pue = 1.0
        
        return {
            "cop": cop,
            "eer": eer,
            "product_min_pue": min_pue,
            "actual_pue": actual_pue,
            "power_usage": 0.0
        }
    
    def _calculate_passive_commercial_metrics(self, cooling_kw: float,
                                           operating_hours: float, electricity_cost: float,
                                           carbon_factor: float) -> Dict[str, Any]:
        """
        Calculate commercial metrics for passive cooling.
        
        Args:
            cooling_kw: Cooling capacity in kW
            operating_hours: Operating hours per year
            electricity_cost: Electricity cost per kWh
            carbon_factor: Carbon emissions factor in kg CO2/kWh
            
        Returns:
            Dictionary containing commercial metrics
        """
        # Passive systems have zero energy consumption
        energy_costs = {
            "power_kw": 0.0,
            "annual_energy_kwh": 0.0,
            "annual_cost": 0.0
        }
        
        # Zero energy means zero direct carbon emissions
        environmental = {
            "annual_carbon_kg": 0.0,
            "tree_equivalent": 0.0,
            "car_equivalent": 0.0
        }
        
        # Estimate traditional cooling energy consumption and costs
        # Assuming a typical active cooling system for comparison
        typical_active_power = 0.1 * cooling_kw * 1000  # W (10% of cooling capacity)
        
        traditional_energy_costs = self.calculate_energy_costs(
            typical_active_power, operating_hours, electricity_cost
        )
        
        # Calculate savings (100% savings compared to traditional)
        annual_savings = traditional_energy_costs["annual_cost"]
        
        # Estimate capital costs
        # Passive systems typically cost more than active ones
        capital_cost = self._estimate_passive_capital_cost(cooling_kw)
        
        # Calculate ROI and payback period
        roi = (annual_savings / capital_cost) * 100 if capital_cost > 0 else float('inf')
        payback_years = capital_cost / annual_savings if annual_savings > 0 else float('inf')
        
        return {
            "energy_costs": energy_costs,
            "environmental": environmental,
            "traditional_energy_costs": traditional_energy_costs,
            "annual_savings": annual_savings,
            "capital_cost": capital_cost,
            "roi_percentage": roi,
            "payback_years": payback_years
        }
    
    def _estimate_passive_capital_cost(self, cooling_kw: float) -> float:
        """
        Estimate capital cost of the passive cooling system.
        
        Args:
            cooling_kw: Cooling capacity in kW
            
        Returns:
            Estimated capital cost
        """
        # This is a simplified model
        # In a real implementation, this would be based on actual pricing data
        # Passive systems are typically more expensive per kW than active ones
        base_cost = 12000  # Base cost for CL21 series
        per_kw_cost = 600  # Cost per kW of cooling capacity
        
        return base_cost + (per_kw_cost * cooling_kw)


class HPCCoolingModel(ActiveCoolingModel):
    """
    Cooling model for high-performance computing rear door heat exchangers (CL23 series).
    
    These models are designed for extreme cooling loads and are more efficient at high capacities.
    Inherits from ActiveCoolingModel with specific overrides for HPC characteristics.
    """
    
    def _calculate_efficiency_metrics(self, cooling_kw: float, power_consumption: float) -> Dict[str, float]:
        """
        Calculate efficiency metrics for HPC cooling.
        
        Overrides ActiveCoolingModel._calculate_efficiency_metrics with HPC-specific calculations.
        
        Args:
            cooling_kw: Cooling capacity in kW
            power_consumption: Power consumption in W
            
        Returns:
            Dictionary containing efficiency metrics
        """
        # Start with normal active cooling calculations
        metrics = super()._calculate_efficiency_metrics(cooling_kw, power_consumption)
        
        # HPC systems are more efficient at higher loads
        # Adjust EER based on load percentage
        max_capacity = self.product.get("max_cooling_capacity", 204.0)
        load_percentage = (cooling_kw / max_capacity) * 100
        
        # At full load, use the rated EER; at lower loads, slightly reduce efficiency
        rated_eer = self.product.get("efficiency", {}).get("eer", 100.0)
        load_factor = 0.7 + (0.3 * load_percentage / 100)  # 70% to 100% of rated EER
        
        metrics["eer"] = rated_eer * load_factor
        
        # Recalculate COP from EER
        # COP = EER / 3.412
        metrics["cop"] = metrics["eer"] / 3.412
        
        # Add HPC-specific metrics
        metrics["hpc_optimized"] = True
        metrics["optimal_load_percentage"] = load_percentage
        metrics["cooling_density"] = cooling_kw / (self.product.get("dimensions", {}).get("width", 800) / 1000)  # kW per meter of rack width
        
        return metrics
