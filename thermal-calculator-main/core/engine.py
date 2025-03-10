# core/engine.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from .constants import DEFAULT_ALTITUDE, DEFAULT_GLYCOL_PERCENTAGE
from .unit_conversion import convert_temperature, convert_power, convert_flow_rate
from ..models.heat_exchanger import HeatExchanger
from ..models.fan import FanSystem
from ..models.piping import PipingSystem
from ..models.valve import ValveSelector
from ..commercial.calculator import CommercialCalculator
from ..analytics.usage_tracker import UsageTracker
from ..utils.regional_data import get_regional_settings

logger = logging.getLogger(__name__)

class CalculationEngine:
    """
    Main calculation engine for the Data Center Cooling Calculator.
    
    This class coordinates the various calculation modules and handles the overall
    workflow from input to output.
    """
    
    def __init__(self, product_database: Dict, regional_database: Dict, 
                 usage_tracker: Optional[UsageTracker] = None):
        """
        Initialize the calculation engine.
        
        Args:
            product_database: Dictionary of product specifications
            regional_database: Dictionary of regional settings and parameters
            usage_tracker: Optional usage tracking component
        """
        self.products = product_database
        self.regional_data = regional_database
        self.usage_tracker = usage_tracker
        
    def calculate(self, cooling_kw: float, room_temp: float, desired_temp: float, 
                  water_temp: float, **kwargs) -> Dict[str, Any]:
        """
        Main calculation entry point requiring only essential inputs.
        
        Args:
            cooling_kw: Required cooling capacity in kilowatts
            room_temp: Current room temperature in °C
            desired_temp: Target room temperature in °C
            water_temp: Supply water temperature in °C
            **kwargs: Additional optional parameters:
                - location: Geographical location for regional settings
                - altitude: Installation altitude in meters
                - fluid_type: Type of cooling fluid ('water', 'ethylene_glycol', 'propylene_glycol')
                - glycol_percentage: Percentage of glycol in mixture (0-100)
                - rack_type: Type of rack ('42U600', '42U800', '48U800', etc.)
                - pipe_configuration: Configuration of piping ('bottom_fed', 'top_fed')
                - voltage: Supply voltage for fans (208V, 230V, etc.)
                - include_commercial: Whether to include commercial calculations
                - units: Preferred units ('metric' or 'imperial')
        
        Returns:
            Dict containing calculation results
        """
        calculation_id = kwargs.get('calculation_id', datetime.now().isoformat())
        logger.info(f"Starting calculation {calculation_id}")
        
        # Get regional settings if location is provided
        location = kwargs.get('location')
        regional_settings = self._get_regional_settings(location)
        
        # Apply default values for unspecified parameters
        altitude = kwargs.get('altitude', DEFAULT_ALTITUDE)
        fluid_type = kwargs.get('fluid_type', regional_settings.get('default_fluid', 'water'))
        glycol_percentage = kwargs.get('glycol_percentage', 
                                      regional_settings.get('default_glycol_percentage', DEFAULT_GLYCOL_PERCENTAGE))
        units = kwargs.get('units', regional_settings.get('preferred_units', 'metric'))
        
        # Convert units if necessary
        if units == 'imperial':
            cooling_kw = convert_power(cooling_kw, 'ton', 'kw')
            room_temp = convert_temperature(room_temp, 'f', 'c')
            desired_temp = convert_temperature(desired_temp, 'f', 'c')
            water_temp = convert_temperature(water_temp, 'f', 'c')
        
        # Select appropriate product based on requirements
        product = self._select_product(cooling_kw, kwargs.get('rack_type'))
        logger.info(f"Selected product: {product['name']}")
        
        # Create system components
        heat_exchanger = self._create_heat_exchanger(product, fluid_type, glycol_percentage)
        fan_system = self._create_fan_system(product, kwargs.get('voltage', regional_settings.get('default_voltage', 230)))
        piping = self._create_piping_system(kwargs.get('pipe_configuration', 'bottom_fed'))
        valve_selector = ValveSelector(product['valve_options'])
        
        # Calculate technical performance
        performance = self._calculate_technical_performance(
            heat_exchanger, fan_system, piping, valve_selector,
            cooling_kw, room_temp, desired_temp, water_temp,
            altitude=altitude,
            **kwargs
        )
        
        # Apply regional adjustments
        performance = self._apply_regional_adjustments(performance, regional_settings)
        
        # Calculate commercial aspects if requested
        if kwargs.get('include_commercial', True):
            commercial_calc = CommercialCalculator(
                regional_settings.get('energy_costs', {'electricity': 0.15}),
                regional_settings.get('carbon_factors', {'electricity': 0.5})
            )
            
            operating_hours = kwargs.get('operating_hours_per_year', 8760)  # Default: 24/7 operation
            lifespan = kwargs.get('lifespan_years', 10)  # Default: 10 year lifespan
            
            performance['commercial'] = {
                'tco': commercial_calc.calculate_tco(performance, operating_hours, lifespan),
                'environmental': commercial_calc.calculate_environmental_impact(
                    performance, operating_hours, lifespan
                )
            }
            
            # Calculate ROI if baseline performance is provided
            baseline = kwargs.get('baseline_performance')
            if baseline:
                performance['commercial']['roi'] = commercial_calc.calculate_roi(
                    performance, baseline, operating_hours, lifespan
                )
        
        # Convert results back to requested units
        if units == 'imperial':
            performance = self._convert_results_to_imperial(performance)
        
        # Track usage for analytics if enabled
        if self.usage_tracker and kwargs.get('track_analytics', True):
            self.usage_tracker.track_calculation(
                {'cooling_kw': cooling_kw, 'room_temp': room_temp, 
                 'desired_temp': desired_temp, 'water_temp': water_temp, **kwargs},
                performance,
                kwargs.get('user_info')
            )
        
        logger.info(f"Completed calculation {calculation_id}")
        return performance
    
    def _get_regional_settings(self, location: Optional[str]) -> Dict[str, Any]:
        """Get regional settings for specified location with appropriate defaults."""
        if not location:
            return {}
            
        return get_regional_settings(self.regional_data, location)
    
    def _select_product(self, cooling_kw: float, rack_type: Optional[str]) -> Dict[str, Any]:
        """
        Select the most appropriate product based on cooling requirements and rack type.
        
        This implements the product selection logic mentioned in the transcript,
        recommending appropriate product sizes based on cooling requirements.
        """
        suitable_products = []
        
        # Filter products by rack type if specified
        candidates = [p for p in self.products.values() 
                     if not rack_type or p['rack_type'] == rack_type]
        
        # Find products that can handle the required cooling
        for product in candidates:
            if cooling_kw <= product['max_cooling_capacity']:
                suitable_products.append(product)
        
        if not suitable_products:
            # No suitable product found, recommend largest available
            return max(candidates, key=lambda p: p['max_cooling_capacity'])
        
        # Find the most efficient product that meets requirements
        return min(suitable_products, key=lambda p: p['max_cooling_capacity'])
    
    def _create_heat_exchanger(self, product: Dict[str, Any], fluid_type: str, glycol_percentage: float) -> HeatExchanger:
        """Create heat exchanger model with appropriate specifications."""
        return HeatExchanger(
            coil_geometry=product['coil_geometry'],
            fluid_type=fluid_type,
            glycol_percentage=glycol_percentage
        )
    
    def _create_fan_system(self, product: Dict[str, Any], voltage: float) -> FanSystem:
        """Create fan system model with appropriate specifications."""
        return FanSystem(
            fan_specs=product['fan_specs'],
            controller_specs=product['controller_specs'],
            num_fans=product['number_of_fans'],
            voltage=voltage
        )
    
    def _create_piping_system(self, configuration: str) -> PipingSystem:
        """Create piping system model with appropriate specifications."""
        return PipingSystem(configuration=configuration)
    
    def _calculate_technical_performance(self, heat_exchanger: HeatExchanger, 
                                        fan_system: FanSystem, 
                                        piping: PipingSystem,
                                        valve_selector: ValveSelector,
                                        cooling_kw: float, 
                                        room_temp: float, 
                                        desired_temp: float, 
                                        water_temp: float,
                                        **kwargs) -> Dict[str, Any]:
        """
        Calculate complete technical performance based on inputs.
        
        This is the main technical calculation that combines all subsystems.
        """
        # Extract additional parameters
        altitude = kwargs.get('altitude', 0)
        
        # Step 1: Calculate water-side parameters
        # For cooling, we need to know either return water temp or flow rate
        # If neither is provided, we'll calculate based on typical delta T
        return_water_temp = kwargs.get('return_water_temp')
        flow_rate = kwargs.get('flow_rate')
        
        if not return_water_temp and not flow_rate:
            # Use typical delta T of 5°C if neither is specified
            return_water_temp = water_temp + 5.0
            
        water_params = heat_exchanger.calculate_performance(
            cooling_kw, water_temp, return_water_temp, flow_rate
        )
        
        # Step 2: Select appropriate valve based on flow rate
        valve_recommendation = valve_selector.select_valve(water_params['flow_rate'])
        
        # Step 3: Calculate piping system pressure drops
        pipe_params = piping.calculate_pressure_drop(
            water_params['flow_rate'],
            heat_exchanger.get_fluid_properties()
        )
        
        # Step 4: Calculate required air flow
        air_flow_required = self._calculate_required_air_flow(
            cooling_kw, room_temp, desired_temp, altitude
        )
        
        # Step 5: Calculate static pressure based on air flow
        static_pressure = self._calculate_static_pressure(air_flow_required)
        
        # Step 6: Calculate fan performance
        fan_params = fan_system.calculate_performance(
            air_flow_required, static_pressure
        )
        
        # Step 7: Calculate overall system efficiency
        efficiency_metrics = self._calculate_efficiency_metrics(
            cooling_kw, fan_params['power_consumption'], water_params
        )
        
        # Combine all results
        return {
            'cooling_capacity': cooling_kw,
            'water_side': water_params,
            'valve_recommendation': valve_recommendation,
            'piping': pipe_params,
            'air_side': fan_params,
            'efficiency': efficiency_metrics,
            'environmental_conditions': {
                'altitude': altitude,
                'room_temperature': room_temp,
                'desired_room_temperature': desired_temp,
                'water_supply_temperature': water_temp
            }
        }
    
    def _calculate_required_air_flow(self, cooling_kw: float, 
                                    room_temp: float, 
                                    desired_temp: float,
                                    altitude: float) -> float:
        """
        Calculate required air flow based on cooling capacity and temperatures.
        
        Uses the formula: Q = m × cp × ΔT
        Where:
            Q = cooling capacity (kW)
            m = mass flow rate of air (kg/s)
            cp = specific heat capacity of air (kJ/kg·K)
            ΔT = temperature difference (K)
            
        Returns:
            Required air flow in cubic meters per hour (m³/h)
        """
        # Constants
        CP_AIR = 1.005  # kJ/kg·K at 20°C
        AIR_DENSITY_SEA_LEVEL = 1.2  # kg/m³ at 20°C
        
        # Adjust air density for altitude
        # ρ = ρ₀ × exp(-g × M × h / (R × T))
        air_density = AIR_DENSITY_SEA_LEVEL * (1 - altitude * 0.0000225)
        
        # Calculate temperature difference
        delta_t = abs(room_temp - desired_temp)
        
        # Calculate mass flow rate needed
        # Q = m × cp × ΔT
        # m = Q / (cp × ΔT)
        mass_flow_rate = cooling_kw / (CP_AIR * delta_t)  # kg/s
        
        # Convert to volumetric flow rate
        volumetric_flow_rate = (mass_flow_rate / air_density) * 3600  # m³/h
        
        return volumetric_flow_rate
    
    def _calculate_static_pressure(self, air_flow: float) -> float:
        """
        Calculate static pressure based on air flow.
        
        This is a simplified calculation that could be enhanced with more detailed
        modeling of the specific product geometries.
        
        Returns:
            Static pressure in Pascals (Pa)
        """
        # Simplified model: static pressure increases with square of flow rate
        # In reality, this would be based on specific product characteristics
        # and would involve more complex calculations
        return 25.0 + 0.05 * (air_flow / 1000) ** 2
    
    def _calculate_efficiency_metrics(self, cooling_kw: float, 
                                     power_consumption: float,
                                     water_params: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate efficiency metrics for the cooling system.
        
        Args:
            cooling_kw: Cooling capacity in kW
            power_consumption: Power consumption in W
            water_params: Water-side parameters
            
        Returns:
            Dictionary of efficiency metrics
        """
        # Convert power to kW for calculation
        power_kw = power_consumption / 1000
        
        # Calculate COP (Coefficient of Performance)
        cop = cooling_kw / power_kw if power_kw > 0 else float('inf')
        
        # Calculate EER (Energy Efficiency Ratio)
        # EER = cooling capacity (BTU/h) / power input (W)
        # 1 kW = 3412.14 BTU/h
        eer = (cooling_kw * 3412.14) / power_consumption if power_consumption > 0 else float('inf')
        
        # Calculate water-side efficiency
        delta_t = abs(water_params['return_temp'] - water_params['supply_temp'])
        water_efficiency = cooling_kw / (water_params['flow_rate'] * delta_t / 860)  # Efficiency factor
        
        return {
            'cop': cop,
            'eer': eer,
            'water_efficiency': water_efficiency
        }
    
    def _apply_regional_adjustments(self, performance: Dict[str, Any], 
                                   regional_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply region-specific adjustments to the performance calculations.
        
        This could include adjustments for local environmental conditions,
        regional standards, etc.
        """
        # This would implement region-specific adjustments based on the regional settings
        # For now, we'll just return the original performance
        return performance
    
    def _convert_results_to_imperial(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """Convert calculation results from metric to imperial units."""
        # Implementation would convert all relevant values to imperial units
        # For brevity, this is not fully implemented here
        return performance

# models/heat_exchanger.py
from typing import Dict, Any, Optional, Tuple
import math
import logging

logger = logging.getLogger(__name__)

class HeatExchanger:
    """
    Heat exchanger model that implements thermal calculations.
    
    This class handles the heat transfer calculations for the cooling system,
    focusing on the fluid-side thermal performance.
    """
    
    def __init__(self, coil_geometry: Dict[str, Any], fluid_type: str = 'water', 
                 glycol_percentage: float = 0):
        """
        Initialize the heat exchanger model.
        
        Args:
            coil_geometry: Dictionary containing coil geometric parameters
            fluid_type: Type of fluid ('water', 'ethylene_glycol', 'propylene_glycol')
            glycol_percentage: Percentage of glycol in mixture (0-100)
        """
        self.geometry = coil_geometry
        self.fluid_type = fluid_type
        self.glycol_percentage = glycol_percentage
        self.fluid_properties = self._get_fluid_properties()
        self.altitude = 0  # Default to sea level
        
    def calculate_performance(self, cooling_kw: float, 
                              supply_temp: float,
                              return_temp: Optional[float] = None, 
                              flow_rate: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate heat exchanger performance based on available inputs.
        
        At least one of return_temp or flow_rate must be provided.
        
        Args:
            cooling_kw: Required cooling capacity in kW
            supply_temp: Supply water temperature in °C
            return_temp: Return water temperature in °C (optional)
            flow_rate: Water flow rate in m³/h (optional)
            
        Returns:
            Dictionary containing calculation results
        """
        logger.info(f"Calculating heat exchanger performance: cooling={cooling_kw}kW, supply_temp={supply_temp}°C")
        
        # We need either return_temp or flow_rate to perform the calculation
        if return_temp is None and flow_rate is None:
            # If neither is provided, assume a typical delta T of 5°C
            return_temp = supply_temp + 5.0
            logger.info(f"Neither return_temp nor flow_rate provided, assuming delta T = 5°C, return_temp = {return_temp}°C")
        
        # Calculate the missing parameter
        if flow_rate is None:
            flow_rate = self._calculate_flow_rate(cooling_kw, supply_temp, return_temp)
            logger.info(f"Calculated flow_rate: {flow_rate} m³/h")
        elif return_temp is None:
            return_temp = self._calculate_return_temp(cooling_kw, supply_temp, flow_rate)
            logger.info(f"Calculated return_temp: {return_temp}°C")
        
        # Calculate pressure drop through the coil
        pressure_drop = self._calculate_pressure_drop(flow_rate)
        
        # Calculate heat transfer coefficient
        htc = self._calculate_heat_transfer_coefficient(flow_rate)
        
        # Calculate approach temperature
        # This is the difference between the outlet water temperature and
        # the inlet air temperature (which would be the room temperature in cooling mode)
        # We'll assume this is provided elsewhere, so using a placeholder here
        approach_temp = 3.0  # Typical value, would be calculated based on air-side conditions
        
        # Calculate nominal thermal power at standard conditions
        # This would be different from the actual cooling capacity at the
        # specified conditions
        nominal_power = self._calculate_nominal_power()
        
        # Calculate effectiveness
        effectiveness = self._calculate_effectiveness(flow_rate)
        
        return {
            'cooling_capacity': cooling_kw,
            'flow_rate': flow_rate,
            'supply_temp': supply_temp,
            'return_temp': return_temp,
            'delta_t': abs(return_temp - supply_temp),
            'pressure_drop': pressure_drop,
            'heat_transfer_coefficient': htc,
            'approach_temperature': approach_temp,
            'nominal_power': nominal_power,
            'effectiveness': effectiveness,
            'fluid_type': self.fluid_type,
            'glycol_percentage': self.glycol_percentage
        }
    
    def get_fluid_properties(self) -> Dict[str, Any]:
        """Get current fluid properties."""
        return self.fluid_properties
    
    def _get_fluid_properties(self) -> Dict[str, float]:
        """
        Get fluid properties based on fluid type and glycol percentage.
        
        Returns:
            Dictionary containing fluid properties:
                - density: Fluid density in kg/m³
                - specific_heat: Specific heat capacity in kJ/kg·K
                - viscosity: Dynamic viscosity in Pa·s
                - thermal_conductivity: Thermal conductivity in W/m·K
        """
        # Base properties for water at 20°C
        water_properties = {
            'density': 998.0,  # kg/m³
            'specific_heat': 4.182,  # kJ/kg·K
            'viscosity': 0.001,  # Pa·s
            'thermal_conductivity': 0.6,  # W/m·K
        }
        
        # If using pure water, return water properties
        if self.fluid_type == 'water' or self.glycol_percentage == 0:
            return water_properties
        
        # For glycol mixtures, adjust properties based on glycol percentage
        # These are simplified approximations and would need more detailed
        # implementation for a real system
        if self.fluid_type == 'ethylene_glycol':
            # Ethylene glycol properties (simplified)
            glycol_factor = self.glycol_percentage / 100.0
            return {
                'density': water_properties['density'] * (1 + 0.13 * glycol_factor),
                'specific_heat': water_properties['specific_heat'] * (1 - 0.45 * glycol_factor),
                'viscosity': water_properties['viscosity'] * (1 + 10 * glycol_factor),
                'thermal_conductivity': water_properties['thermal_conductivity'] * (1 - 0.3 * glycol_factor),
            }
        elif self.fluid_type == 'propylene_glycol':
            # Propylene glycol properties (simplified)
            glycol_factor = self.glycol_percentage / 100.0
            return {
                'density': water_properties['density'] * (1 + 0.06 * glycol_factor),
                'specific_heat': water_properties['specific_heat'] * (1 - 0.4 * glycol_factor),
                'viscosity': water_properties['viscosity'] * (1 + 15 * glycol_factor),
                'thermal_conductivity': water_properties['thermal_conductivity'] * (1 - 0.35 * glycol_factor),
            }
        else:
            # Unknown fluid type, return water properties
            logger.warning(f"Unknown fluid type: {self.fluid_type}, using water properties")
            return water_properties
    
    def _calculate_flow_rate(self, cooling_kw: float, supply_temp: float, return_temp: float) -> float:
        """
        Calculate required flow rate based on cooling capacity and temperatures.
        
        Uses the formula: Q = ṁ × cp × ΔT
        Where:
            Q = cooling capacity (kW)
            ṁ = mass flow rate (kg/s)
            cp = specific heat capacity (kJ/kg·K)
            ΔT = temperature difference (K)
            
        Returns:
            Flow rate in m³/h
        """
        # Calculate temperature difference
        delta_t = abs(return_temp - supply_temp)
        
        # Get fluid properties
        density = self.fluid_properties['density']
        specific_heat = self.fluid_properties['specific_heat']
        
        # Calculate mass flow rate (kg/s)
        # Q = ṁ × cp × ΔT
        # ṁ = Q / (cp × ΔT)
        mass_flow_rate = cooling_kw / (specific_heat * delta_t)
        
        # Convert to volume flow rate (m³/h)
        # ṁ = ρ × V̇
        # V̇ = ṁ / ρ
        volume_flow_rate = (mass_flow_rate / density) * 3600
        
        return volume_flow_rate
    
    def _calculate_return_temp(self, cooling_kw: float, supply_temp: float, flow_rate: float) -> float:
        """
        Calculate return temperature based on cooling capacity and flow rate.
        
        Uses the formula: Q = ṁ × cp × ΔT
        Where:
            Q = cooling capacity (kW)
            ṁ = mass flow rate (kg/s)
            cp = specific heat capacity (kJ/kg·K)
            ΔT = temperature difference (K)
            
        Returns:
            Return temperature in °C
        """
        # Get fluid properties
        density = self.fluid_properties['density']
        specific_heat = self.fluid_properties['specific_heat']
        
        # Convert volume flow rate (m³/h) to mass flow rate (kg/s)
        mass_flow_rate = (flow_rate * density) / 3600
        
        # Calculate temperature difference
        # Q = ṁ × cp × ΔT
        # ΔT = Q / (ṁ × cp)
        delta_t = cooling_kw / (mass_flow_rate * specific_heat)
        
        # For cooling, return temperature is higher than supply temperature
        return supply_temp + delta_t
    
    def _calculate_pressure_drop(self, flow_rate: float) -> float:
        """
        Calculate pressure drop through the heat exchanger.
        
        This would implement detailed pressure drop calculations based on:
        - Coil geometry
        - Flow rate
        - Fluid properties
        
        Returns:
            Pressure drop in kPa
        """
        # Simplified calculation based on flow rate
        # In a real implementation, this would involve more detailed calculations
        # based on the specific coil geometry, fluid properties, and flow regime
        
        # Get fluid properties
        density = self.fluid_properties['density']
        viscosity = self.fluid_properties['viscosity']
        
        # Get coil geometry parameters
        tube_diameter = self.geometry['tube_diameter']  # mm
        tube_length = self.geometry['tube_length']  # m
        number_of_passes = self.geometry['number_of_passes']
        
        # Convert tube diameter to meters
        tube_diameter_m = tube_diameter / 1000
        
        # Calculate flow velocity
        # V = Q / A
        # where Q is in m³/s and A is in m²
        flow_rate_m3s = flow_rate / 3600
        tube_area = math.pi * (tube_diameter_m / 2) ** 2
        velocity = flow_rate_m3s / tube_area
        
        # Calculate Reynolds number
        # Re = ρ × V × D / μ
        reynolds = (density * velocity * tube_diameter_m) / viscosity
        
        # Calculate friction factor
        # For laminar flow (Re < 2300)
        if reynolds < 2300:
            friction_factor = 64 / reynolds
        else:
            # For turbulent flow, using Blasius correlation (simplified)
            friction_factor = 0.316 * reynolds ** (-0.25)
        
        # Calculate pressure drop using Darcy-Weisbach equation
        # ΔP = f × (L/D) × (ρ × V²/2)
        pressure_drop = friction_factor * (tube_length * number_of_passes / tube_diameter_m) * (density * velocity ** 2 / 2)
        
        # Convert to kPa
        pressure_drop_kpa = pressure_drop / 1000
        
        return pressure_drop_kpa
    
    def _calculate_heat_transfer_coefficient(self, flow_rate: float) -> float:
        """
        Calculate overall heat transfer coefficient.
        
        This would implement detailed heat transfer calculations based on:
        - Coil geometry
        - Flow rate
        - Fluid properties
        
        Returns:
            Heat transfer coefficient in W/m²·K
        """
        # This is a simplified placeholder calculation
        # In a real implementation, this would involve more detailed calculations
        # including both water-side and air-side heat transfer coefficients
        
        # Simplified calculation that scales with flow rate
        base_htc = 1500  # W/m²·K
        flow_factor = (flow_rate / 5.0) ** 0.8  # Scaling with flow rate
        
        return base_htc * flow_factor
    
    def _calculate_nominal_power(self) -> float:
        """
        Calculate nominal thermal power at standard conditions.
        
        Returns:
            Nominal thermal power in kW
        """
        # This would use the coil geometry and standard conditions
        # to calculate the nominal power
        # Simplified placeholder calculation
        tube_length = self.geometry['tube_length']
        fin_area = self.geometry['fin_area']
        tube_rows = self.geometry['tube_rows']
        
        # Simplified nominal power calculation
        nominal_power = 10 * tube_rows * fin_area * tube_length / 10
        
        return nominal_power
    
    def _calculate_effectiveness(self, flow_rate: float) -> float:
        """
        Calculate heat exchanger effectiveness using ε-NTU method.
        
        Returns:
            Effectiveness (dimensionless, 0-1)
        """
        # This would implement the ε-NTU method for heat exchanger effectiveness
        # Simplified placeholder calculation
        base_effectiveness = 0.65
        flow_factor = 1.0 + 0.1 * math.log(flow_rate / 5.0) if flow_rate > 0 else 0
        
        effectiveness = base_effectiveness * flow_factor
        
        # Ensure effectiveness is between 0 and 1
        return max(0.0, min(1.0, effectiveness))
    
    def adjust_for_altitude(self, altitude: float) -> None:
        """
        Adjust calculations for installation altitude.
        
        Args:
            altitude: Installation altitude in meters
        """
        self.altitude = altitude
        
        # In a real implementation, this would adjust various calculations
        # to account for changes in air density, pressure, etc. at different altitudes

# models/fan.py
from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger(__name__)

class FanSystem:
    """
    Fan system model that implements air-side calculations.
    
    This class handles fan performance, power consumption, and noise level calculations
    for the cooling system, focusing on the air-side performance.
    """
    
    def __init__(self, fan_specs: Dict[str, Any], controller_specs: Dict[str, Any],
                 num_fans: int = 1, voltage: float = 230):
        """
        Initialize the fan system model.
        
        Args:
            fan_specs: Dictionary containing fan specifications
            controller_specs: Dictionary containing controller specifications
            num_fans: Number of fans in the system
            voltage: Supply voltage (V)
        """
        self.fan_specs = fan_specs
        self.controller = controller_specs
        self.num_fans = num_fans
        self.voltage = voltage
        
        # Normalize voltage factor
        self.voltage_factor = self._calculate_voltage_factor(voltage)
        
    def calculate_performance(self, air_flow: float, static_pressure: float) -> Dict[str, Any]:
        """
        Calculate fan performance for required air flow and static pressure.
        
        Args:
            air_flow: Required air flow in m³/h
            static_pressure: Static pressure in Pa
            
        Returns:
            Dictionary containing fan performance parameters
        """
        logger.info(f"Calculating fan performance: air_flow={air_flow}m³/h, static_pressure={static_pressure}Pa")
        
        # Calculate required fan speed
        fan_speed_percentage = self._calculate_required_fan_speed(air_flow, static_pressure)
        
        # Calculate power consumption
        power_consumption = self._calculate_power_consumption(fan_speed_percentage)
        
        # Calculate noise level
        noise_level = self._calculate_noise_level(fan_speed_percentage)
        
        # Check if fans can meet the requirements
        max_air_flow = self.fan_specs['max_air_flow'] * self.num_fans
        max_static_pressure = self.fan_specs['max_static_pressure']
        
        fan_sufficient = (air_flow <= max_air_flow and static_pressure <= max_static_pressure)
        
        return {
            'fan_speed_percentage': fan_speed_percentage,
            'air_flow': air_flow,
            'static_pressure': static_pressure,
            'power_consumption': power_consumption,
            'noise_level': noise_level,
            'number_of_fans': self.num_fans,
            'fan_sufficient': fan_sufficient,
            'max_air_flow': max_air_flow,
            'max_static_pressure': max_static_pressure
        }
    
    def _calculate_voltage_factor(self, voltage: float) -> float:
        """
        Calculate voltage adjustment factor.
        
        Different voltage levels (e.g., 208V in US vs 230V in EU) affect
        fan performance.
        
        Args:
            voltage: Supply voltage in V
            
        Returns:
            Voltage adjustment factor (dimensionless)
        """
        # Normalize to 230V (European standard)
        return (voltage / 230.0) ** 2
    
    def _calculate_required_fan_speed(self, air_flow: float, static_pressure: float) -> float:
        """
        Calculate required fan speed percentage to achieve desired flow and pressure.
        
        Uses fan laws to determine the required fan speed.
        
        Args:
            air_flow: Required air flow in m³/h
            static_pressure: Static pressure in Pa
            
        Returns:
            Fan speed as percentage of maximum (0-100)
        """
        # Get fan specifications
        nominal_air_flow = self.fan_specs['nominal_air_flow']
        nominal_static_pressure = self.fan_specs['nominal_static_pressure']
        
        # Adjust for number of fans
        system_nominal_air_flow = nominal_air_flow * self.num_fans
        
        # Calculate required speed for air flow using fan laws
        # Q2/Q1 = N2/N1
        flow_speed_ratio = air_flow / system_nominal_air_flow if system_nominal_air_flow > 0 else 0
        
        # Calculate required speed for static pressure using fan laws
        # P2/P1 = (N2/N1)²
        pressure_speed_ratio = math.sqrt(static_pressure / nominal_static_pressure) if nominal_static_pressure > 0 else 0
        
        # Use the higher of the two ratios to ensure both requirements are met
        speed_ratio = max(flow_speed_ratio, pressure_speed_ratio)
        
        # Convert to percentage
        fan_speed_percentage = speed_ratio * 100
        
        # Ensure speed is between 0 and 100%
        fan_speed_percentage = max(0.0, min(100.0, fan_speed_percentage))
        
        return fan_speed_percentage
    
    def _calculate_power_consumption(self, fan_speed_percentage: float) -> float:
        """
        Calculate power consumption based on fan speed.
        
        Uses fan laws to determine power consumption at a given speed.
        
        Args:
            fan_speed_percentage: Fan speed as percentage of maximum (0-100)
            
        Returns:
            Power consumption in W
        """
        # Get fan specifications
        nominal_power = self.fan_specs['nominal_power']
        
        # Calculate speed ratio
        speed_ratio = fan_speed_percentage / 100.0
        
        # Calculate power using fan laws
        # W2/W1 = (N2/N1)³
        power_ratio = speed_ratio ** 3
        
        # Calculate power consumption
        power_consumption = nominal_power * power_ratio * self.num_fans
        
        # Adjust for voltage
        power_consumption *= self.voltage_factor
        
        return power_consumption
    
    def _calculate_noise_level(self, fan_speed_percentage: float) -> float:
        """
        Calculate noise level based on fan speed.
        
        Args:
            fan_speed_percentage: Fan speed as percentage of maximum (0-100)
            
        Returns:
            Noise level in dB(A)
        """
        # Get fan specifications
        nominal_noise = self.fan_specs['nominal_noise']
        
        # Calculate speed ratio
        speed_ratio = fan_speed_percentage / 100.0
        
        # Noise level typically increases with log of speed
        # This is a simplified model
        noise_level = nominal_noise + 20 * math.log10(speed_ratio) if speed_ratio > 0 else 0
        
        # Adjust for multiple fans
        # Adding 3 dB for each doubling of fans
        noise_adjustment = 10 * math.log10(self.num_fans)
        total_noise = noise_level + noise_adjustment
        
        return max(0, total_noise)
    
    def recommend_fan_configuration(self, cooling_required: float, static_pressure: float) -> Dict[str, Any]:
        """
        Recommend optimal fan configuration.
        
        Args:
            cooling_required: Required cooling capacity in kW
            static_pressure: Static pressure in Pa
            
        Returns:
            Dictionary containing recommended fan configuration
        """
        # This would implement logic to determine the optimal number of fans
        # and speed settings based on the cooling requirements and static pressure
        
        # Simplified placeholder implementation
        required_air_flow = cooling_required * 300  # Simplified conversion
        
        # Calculate performance with current configuration
        performance = self.calculate_performance(required_air_flow, static_pressure)
        
        # Check if current configuration is sufficient
        if not performance['fan_sufficient']:
            # Recommend increasing number of fans
            recommended_fans = math.ceil(required_air_flow / self.fan_specs['max_air_flow'])
            
            return {
                'current_performance': performance,
                'recommended_fans': recommended_fans,
                'recommendation': f"Current fan configuration is insufficient. Consider using {recommended_fans} fans."
            }
        
        # Check if current configuration is inefficient
        if performance['fan_speed_percentage'] < 50:
            # Recommend reducing number of fans
            recommended_fans = max(1, math.ceil(self.num_fans * performance['fan_speed_percentage'] / 80))
            
            return {
                'current_performance': performance,
                'recommended_fans': recommended_fans,
                'recommendation': f"Current fan configuration may be inefficient. Consider using {recommended_fans} fans at higher speed."
            }
        
        # Current configuration is appropriate
        return {
            'current_performance': performance,
            'recommended_fans': self.num_fans,
            'recommendation': "Current fan configuration is appropriate."
        }

# models/piping.py
from typing import Dict, Any, Optional
import math
import logging

logger = logging.getLogger(__name__)

class PipingSystem:
    """
    Piping system model that implements fluid dynamics calculations.
    
    This class handles pressure drop calculations for the piping system,
    including straight pipes, bends, and fittings.
    """
    
    def __init__(self, configuration: str = 'bottom_fed', pipe_length: float = 3.7,
                 pipe_diameter: float = 25.0, num_bends: int = 0):
        """
        Initialize the piping system model.
        
        Args:
            configuration: Pipe configuration ('bottom_fed', 'top_fed')
            pipe_length: Length of pipes in meters
            pipe_diameter: Diameter of pipes in mm
            num_bends: Number of additional bends beyond those in standard configuration
        """
        self.configuration = configuration
        self.pipe_length = pipe_length
        self.pipe_diameter = pipe_diameter
        self.num_bends = num_bends
        
        # Set default bend configuration based on pipe configuration
        self.bend_angles = self._get_default_bend_configuration()
        
    def calculate_pressure_drop(self, flow_rate: float, fluid_properties: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate pressure drop through the piping system.
        
        Args:
            flow_rate: Flow rate in m³/h
            fluid_properties: Dictionary containing fluid properties
            
        Returns:
            Dictionary containing pressure drop calculations
        """
        logger.info(f"Calculating piping pressure drop: flow_rate={flow_rate}m³/h, configuration={self.configuration}")
        
        # Extract fluid properties
        density = fluid_properties['density']
        viscosity = fluid_properties['viscosity']
        
        # Calculate straight pipe pressure drop
        straight_drop = self._calculate_straight_pipe_drop(
            flow_rate, self.pipe_length, self.pipe_diameter, density, viscosity
        )
        
        # Calculate bend pressure drop
        bend_drop = self._calculate_bend_pressure_drop(
            flow_rate, self.bend_angles, self.pipe_diameter, density, viscosity
        )
        
        # Calculate additional fittings pressure drop
        # This is a placeholder for additional fittings like valves, filters, etc.
        fittings_drop = 0.0
        
        # Calculate total pressure drop
        total_drop = straight_drop + bend_drop + fittings_drop
        
        return {
            'total_pressure_drop': total_drop,
            'straight_pipe_drop': straight_drop,
            'bend_pressure_drop': bend_drop,
            'fittings_pressure_drop': fittings_drop,
            'configuration': self.configuration,
            'pipe_length': self.pipe_length,
            'pipe_diameter': self.pipe_diameter
        }
    
    def _get_default_bend_configuration(self) -> Dict[int, int]:
        """
        Get default bend configuration based on pipe configuration.
        
        Returns:
            Dictionary mapping bend angles to counts
        """
        if self.configuration == 'top_fed':
            # Top-fed configuration typically has two 90° bends
            # as mentioned in the transcript
            return {90: 2, 180: 0}
        else:
            # Bottom-fed configuration typically has minimal bends
            return {90: 0, 180: 0}
    
    def _calculate_straight_pipe_drop(self, flow_rate: float, pipe_length: float,
                                     pipe_diameter: float, density: float,
                                     viscosity: float) -> float:
        """
        Calculate pressure drop in straight pipe.
        
        Uses the Darcy-Weisbach equation:
        ΔP = f × (L/D) × (ρ × v²/2)
        
        Args:
            flow_rate: Flow rate in m³/h
            pipe_length: Pipe length in m
            pipe_diameter: Pipe diameter in mm
            density: Fluid density in kg/m³
            viscosity: Fluid viscosity in Pa·s
            
        Returns:
            Pressure drop in kPa
        """
        # Convert units
        pipe_diameter_m = pipe_diameter / 1000  # mm to m
        flow_rate_m3s = flow_rate / 3600  # m³/h to m³/s
        
        # Calculate flow velocity
        pipe_area = math.pi * (pipe_diameter_m / 2) ** 2
        velocity = flow_rate_m3s / pipe_area if pipe_area > 0 else 0
        
        # Calculate Reynolds number
        reynolds = (density * velocity * pipe_diameter_m) / viscosity if viscosity > 0 else 0
        
        # Calculate friction factor
        if reynolds < 2300:
            # Laminar flow
            friction_factor = 64 / reynolds if reynolds > 0 else 0
        else:
            # Turbulent flow (simplified Colebrook equation)
            # Using Haaland equation as an explicit approximation
            relative_roughness = 0.0002 / pipe_diameter_m  # Assumed pipe roughness of 0.0002 m
            friction_factor = (-1.8 * math.log10((relative_roughness/3.7)**1.11 + 6.9/reynolds))**(-2)
        
        # Calculate pressure drop using Darcy-Weisbach equation
        pressure_drop = friction_factor * (pipe_length / pipe_diameter_m) * (density * velocity**2 / 2)
        
        # Convert to kPa
        pressure_drop_kpa = pressure_drop / 1000
        
        return pressure_drop_kpa
    
    def _calculate_bend_pressure_drop(self, flow_rate: float, bend_angles: Dict[int, int],
                                     pipe_diameter: float, density: float,
                                     viscosity: float) -> float:
        """
        Calculate pressure drop in pipe bends.
        
        Args:
            flow_rate: Flow rate in m³/h
            bend_angles: Dictionary mapping bend angles to counts
            pipe_diameter: Pipe diameter in mm
            density: Fluid density in kg/m³
            viscosity: Fluid viscosity in Pa·s
            
        Returns:
            Pressure drop in kPa
        """
        # Convert units
        pipe_diameter_m = pipe_diameter / 1000  # mm to m
        flow_rate_m3s = flow_rate / 3600  # m³/h to m³/s
        
        # Calculate flow velocity
        pipe_area = math.pi * (pipe_diameter_m / 2) ** 2
        velocity = flow_rate_m3s / pipe_area if pipe_area > 0 else 0
        
        # Calculate pressure drop for each bend type
        total_bend_drop = 0.0
        
        for angle, count in bend_angles.items():
            # Get K factor based on bend angle
            k_factor = self._get_bend_k_factor(angle)
            
            # Calculate pressure drop
            # ΔP = K × (ρ × v²/2)
            bend_drop = k_factor * (density * velocity**2 / 2) * count
            
            total_bend_drop += bend_drop
        
        # Convert to kPa
        total_bend_drop_kpa = total_bend_drop / 1000
        
        return total_bend_drop_kpa
    
    def _get_bend_k_factor(self, angle: int) -> float:
        """
        Get K factor for bend based on angle.
        
        Args:
            angle: Bend angle in degrees
            
        Returns:
            K factor (dimensionless)
        """
        # K factors for standard bends with r/d ≈ 1.5
        k_factors = {
            45: 0.35,
            90: 0.75,
            180: 1.5
        }
        
        # Return K factor for specified angle, or 0 if not found
        return k_factors.get(angle, 0.0)

# models/valve.py
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ValveSelector:
    """
    Valve selector that recommends appropriate valves based on flow rate.
    
    This class implements the valve selection logic mentioned in the transcript,
    recommending the appropriate valve size and type based on the required flow rate.
    """
    
    def __init__(self, valve_options: List[Dict[str, Any]]):
        """
        Initialize the valve selector.
        
        Args:
            valve_options: List of available valve options
        """
        self.valve_options = sorted(valve_options, key=lambda v: v['max_flow_rate'])
        
    def select_valve(self, flow_rate: float) -> Dict[str, Any]:
        """
        Select the appropriate valve based on flow rate.
        
        Args:
            flow_rate: Flow rate in m³/h
            
        Returns:
            Dictionary containing valve recommendation
        """
        logger.info(f"Selecting valve for flow_rate={flow_rate}m³/h")
        
        # Find smallest valve that can handle the flow rate
        selected_valve = None
        for valve in self.valve_options:
            if flow_rate <= valve['max_flow_rate']:
                selected_valve = valve
                break
        
        # If no valve can handle the flow rate, recommend the largest available
        if selected_valve is None:
            selected_valve = self.valve_options[-1]
            sufficient = False
        else:
            sufficient = True
        
        # Calculate valve utilization percentage
        utilization = (flow_rate / selected_valve['max_flow_rate']) * 100 if selected_valve['max_flow_rate'] > 0 else 0
        
        # Calculate recommended valve settings
        # As mentioned in the transcript, setting the operational range to 40-80% of the nominal flow
        nominal_setting = utilization
        min_setting = max(0, nominal_setting - 20)
        max_setting = min(100, nominal_setting + 20)
        
        return {
            'valve_type': selected_valve['type'],
            'valve_size': selected_valve['size'],
            'max_flow_rate': selected_valve['max_flow_rate'],
            'sufficient': sufficient,
            'utilization_percentage': utilization,
            'recommended_settings': {
                'nominal': nominal_setting,
                'min': min_setting,
                'max': max_setting
            }
        }
    
    def select_valve_by_type(self, flow_rate: float, valve_type: str) -> Dict[str, Any]:
        """
        Select valve of a specific type based on flow rate.
        
        Args:
            flow_rate: Flow rate in m³/h
            valve_type: Type of valve ('2way', 'epiv', etc.)
            
        Returns:
            Dictionary containing valve recommendation
        """
        # Filter valve options by type
        type_options = [v for v in self.valve_options if v['type'] == valve_type]
        
        # If no valves of the specified type exist, return None
        if not type_options:
            return {
                'error': f"No valves of type '{valve_type}' available",
                'available_types': list(set(v['type'] for v in self.valve_options))
            }
        
        # Create a temporary ValveSelector with only the valves of the specified type
        selector = ValveSelector(type_options)
        
        # Select valve
        return selector.select_valve(flow_rate)

# commercial/calculator.py
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CommercialCalculator:
    """
    Commercial calculator that implements business and financial calculations.
    
    This class handles ROI, TCO, and environmental impact calculations for the
    cooling system.
    """
    
    def __init__(self, energy_costs: Dict[str, float], carbon_factors: Dict[str, float]):
        """
        Initialize the commercial calculator.
        
        Args:
            energy_costs: Dictionary mapping energy types to costs (e.g., {'electricity': 0.15})
            carbon_factors: Dictionary mapping energy types to carbon factors
        """
        self.energy_costs = energy_costs
        self.carbon_factors = carbon_factors
        
    def calculate_tco(self, technical_performance: Dict[str, Any], 
                      operating_hours: float, lifespan: float) -> Dict[str, Any]:
        """
        Calculate Total Cost of Ownership.
        
        Args:
            technical_performance: Dictionary containing technical performance results
            operating_hours: Operating hours per year
            lifespan: Expected lifespan in years
            
        Returns:
            Dictionary containing TCO calculations
        """
        logger.info(f"Calculating TCO for {lifespan} years")
        
        # Calculate annual energy consumption
        annual_energy = self._calculate_annual_energy(technical_performance, operating_hours)
        
        # Calculate energy costs
        annual_energy_cost = annual_energy * self.energy_costs.get('electricity', 0.15)
        lifetime_energy_cost = annual_energy_cost * lifespan
        
        # Estimate capital costs
        capital_cost = self._estimate_capital_cost(technical_performance)
        
        # Estimate maintenance costs
        annual_maintenance = self._estimate_maintenance_cost(technical_performance)
        lifetime_maintenance = annual_maintenance * lifespan
        
        # Calculate total costs
        total_cost = capital_cost + lifetime_energy_cost + lifetime_maintenance
        
        # Calculate payback period (simplified)
        # This would normally be compared against a baseline system
        baseline_annual_cost = annual_energy_cost * 1.3  # Assume 30% higher energy cost for baseline
        annual_savings = baseline_annual_cost - annual_energy_cost
        payback_period = capital_cost / annual_savings if annual_savings > 0 else float('inf')
        
        return {
            'total_cost': total_cost,
            'capital_cost': capital_cost,
            'annual_energy_cost': annual_energy_cost,
            'lifetime_energy_cost': lifetime_energy_cost,
            'annual_maintenance': annual_maintenance,
            'lifetime_maintenance': lifetime_maintenance,
            'annual_energy_consumption': annual_energy,
            'payback_period': payback_period
        }
    
    def calculate_roi(self, new_performance: Dict[str, Any], baseline_performance: Dict[str, Any],
                      operating_hours: float, lifespan: float) -> Dict[str, Any]:
        """
        Calculate Return on Investment compared to baseline system.
        
        Args:
            new_performance: Dictionary containing new system technical performance
            baseline_performance: Dictionary containing baseline system performance
            operating_hours: Operating hours per year
            lifespan: Expected lifespan in years
            
        Returns:
            Dictionary containing ROI calculations
        """
        logger.info(f"Calculating ROI compared to baseline system")
        
        # Calculate TCO for both systems
        new_tco = self.calculate_tco(new_performance, operating_hours, lifespan)
        baseline_tco = self.calculate_tco(baseline_performance, operating_hours, lifespan)
        
        # Calculate lifetime savings
        lifetime_savings = baseline_tco['total_cost'] - new_tco['total_cost']
        
        # Calculate annual savings
        annual_savings = (baseline_tco['annual_energy_cost'] + baseline_tco['annual_maintenance']) - \
                         (new_tco['annual_energy_cost'] + new_tco['annual_maintenance'])
        
        # Calculate ROI
        roi_percentage = (lifetime_savings / new_tco['capital_cost']) * 100 if new_tco['capital_cost'] > 0 else float('inf')
        
        # Calculate payback period
        payback_period = new_tco['capital_cost'] / annual_savings if annual_savings > 0 else float('inf')
        
        return {
            'lifetime_savings': lifetime_savings,
            'annual_savings': annual_savings,
            'roi_percentage': roi_percentage,
            'payback_period': payback_period,
            'baseline_total_cost': baseline_tco['total_cost'],
            'new_total_cost': new_tco['total_cost']
        }
    
    def calculate_environmental_impact(self, technical_performance: Dict[str, Any],
                                      operating_hours: float, lifespan: float) -> Dict[str, Any]:
        """
        Calculate environmental impact metrics.
        
        Args:
            technical_performance: Dictionary containing technical performance results
            operating_hours: Operating hours per year
            lifespan: Expected lifespan in years
            
        Returns:
            Dictionary containing environmental impact calculations
        """
        logger.info(f"Calculating environmental impact for {lifespan} years")
        
        # Calculate annual energy consumption
        annual_energy = self._calculate_annual_energy(technical_performance, operating_hours)
        
        # Calculate carbon emissions
        annual_carbon = annual_energy * self.carbon_factors.get('electricity', 0.5)  # kgCO2/kWh
        lifetime_carbon = annual_carbon * lifespan
        
        # Convert to equivalent metrics
        # These values are mentioned in the transcript as being used
        # from the US EPA website
        tree_equivalent = lifetime_carbon * 0.039  # Trees needed to absorb carbon
        car_equivalent = lifetime_carbon / 4600  # Cars removed for a year
        
        return {
            'annual_energy': annual_energy,
            'annual_carbon': annual_carbon,
            'lifetime_carbon': lifetime_carbon,
            'tree_equivalent': tree_equivalent,
            'car_equivalent': car_equivalent
        }
    
    def _calculate_annual_energy(self, technical_performance: Dict[str, Any],
                                operating_hours: float) -> float:
        """
        Calculate annual energy consumption.
        
        Args:
            technical_performance: Dictionary containing technical performance results
            operating_hours: Operating hours per year
            
        Returns:
            Annual energy consumption in kWh
        """
        # Extract power consumption
        if 'air_side' in technical_performance and 'power_consumption' in technical_performance['air_side']:
            # Power consumption is typically in W
            power_kw = technical_performance['air_side']['power_consumption'] / 1000
        else:
            # Use a default value or estimation
            power_kw = technical_performance.get('total_power_consumption', 0) / 1000
        
        # Calculate annual energy
        annual_energy_kwh = power_kw * operating_hours
        
        return annual_energy_kwh
    
    def _estimate_capital_cost(self, technical_performance: Dict[str, Any]) -> float:
        """
        Estimate capital costs based on system specifications.
        
        Args:
            technical_performance: Dictionary containing technical performance results
            
        Returns:
            Estimated capital cost
        """
        # This would implement a detailed cost model based on:
        # - Cooling capacity
        # - System type
        # - Component costs
        
        # Simplified placeholder calculation
        cooling_capacity = technical_performance.get('cooling_capacity', 0)
        base_cost = 5000  # Base cost for any system
        capacity_cost = cooling_capacity * 300  # Cost per kW of cooling
        
        return base_cost + capacity_cost
    
    def _estimate_maintenance_cost(self, technical_performance: Dict[str, Any]) -> float:
        """
        Estimate annual maintenance costs.
        
        Args:
            technical_performance: Dictionary containing technical performance results
            
        Returns:
            Estimated annual maintenance cost
        """
        # This would implement a detailed maintenance cost model based on:
        # - System complexity
        # - Component count
        # - Service requirements
        
        # Simplified placeholder calculation
        capital_cost = self._estimate_capital_cost(technical_performance)
        maintenance_percentage = 0.05  # 5% of capital cost per year
        
        return capital_cost * maintenance_percentage
