"""
Valve model for the Data Center Cooling Calculator.
"""

import math


class Valve:
    """
    Model for control valves in cooling systems.
    """
    
    def __init__(self):
        """Initialize the valve model"""
        # Default parameters
        self.kv = 6.0          # Flow coefficient in m³/h/bar^0.5
        self.valve_type = "globe"
        self.valve_size = 25   # Valve size in mm
        self.opening = 100     # Valve opening percentage (0-100)
        
    def calculate_pressure_drop(self, flow_rate, fluid_type="water", temperature=20, 
                               glycol_percentage=0):
        """
        Calculate pressure drop across the valve
        
        Args:
            flow_rate (float): Water flow rate in m³/h
            fluid_type (str): Type of fluid (water, propylene_glycol, ethylene_glycol)
            temperature (float): Fluid temperature in °C
            glycol_percentage (int): Percentage of glycol in mixture
            
        Returns:
            float: Pressure drop in kPa
        """
        # Adjust Kv for valve opening
        effective_kv = self.kv * self.get_opening_characteristic(self.opening)
        
        # Get specific gravity of fluid
        _, density = self.get_fluid_properties(fluid_type, temperature, glycol_percentage)
        specific_gravity = density / 1000  # Relative to water
        
        # Calculate pressure drop using the Kv formula
        # ΔP (bar) = (Q / Kv)² * SG
        pressure_drop_bar = (flow_rate / effective_kv) ** 2 * specific_gravity
        
        # Convert from bar to kPa
        pressure_drop_kpa = pressure_drop_bar * 100
        
        return pressure_drop_kpa
    
    def get_fluid_properties(self, fluid_type, temperature, glycol_percentage):
        """
        Get fluid viscosity and density
        
        Args:
            fluid_type (str): Type of fluid
            temperature (float): Fluid temperature in °C
            glycol_percentage (int): Percentage of glycol in mixture
            
        Returns:
            tuple: (viscosity in Pa·s, density in kg/m³)
        """
        if fluid_type == "water":
            # Approximate water properties as a function of temperature
            viscosity = 0.001 * math.exp(-0.02 * (temperature - 20))  # Pa·s
            density = 1000 - 0.1 * (temperature - 20)  # kg/m³
        elif fluid_type == "propylene_glycol":
            # Approximate propylene glycol mixture properties
            base_viscosity = 0.001 * math.exp(-0.02 * (temperature - 20))  # Pa·s
            glycol_factor = 1 + 0.1 * glycol_percentage  # viscosity increases with glycol percentage
            temp_factor = math.exp(-0.03 * temperature)  # viscosity decreases with temperature
            viscosity = base_viscosity * glycol_factor * temp_factor
            
            base_density = 1000 - 0.1 * (temperature - 20)  # kg/m³
            density = base_density + glycol_percentage * 1.5
        elif fluid_type == "ethylene_glycol":
            # Approximate ethylene glycol mixture properties
            base_viscosity = 0.001 * math.exp(-0.02 * (temperature - 20))  # Pa·s
            glycol_factor = 1 + 0.08 * glycol_percentage  # viscosity increases with glycol percentage
            temp_factor = math.exp(-0.025 * temperature)  # viscosity decreases with temperature
            viscosity = base_viscosity * glycol_factor * temp_factor
            
            base_density = 1000 - 0.1 * (temperature - 20)  # kg/m³
            density = base_density + glycol_percentage * 1.8
        else:
            # Default to water properties
            viscosity = 0.001  # Pa·s
            density = 1000  # kg/m³
        
        return viscosity, density
    
    def get_opening_characteristic(self, opening_percentage):
        """
        Get flow characteristic based on valve opening percentage
        
        Args:
            opening_percentage (float): Valve opening percentage (0-100)
            
        Returns:
            float: Flow characteristic multiplier (0-1)
        """
        # Normalize opening percentage to 0-1 range
        x = opening_percentage / 100
        
        if self.valve_type == "globe":
            # Equal percentage characteristic
            # y = R^(x-1) where R is the rangeability (typically 50)
            rangeability = 50
            if x < 0.01:
                return 0.01  # Minimum opening
            else:
                return rangeability ** (x - 1)
        elif self.valve_type == "ball":
            # Modified equal percentage characteristic for ball valves
            # Simplified approximation
            if x < 0.1:
                return 0.1 * x / 0.1  # Linear from 0 to 0.1
            else:
                # Equal percentage after 10% opening
                rangeability = 30
                return 0.1 + 0.9 * (rangeability ** ((x - 0.1) / 0.9 - 1))
        elif self.valve_type == "butterfly":
            # S-curve characteristic typical for butterfly valves
            # Using a sigmoid function: y = 1 / (1 + exp(-k*(x-x0)))
            k = 10  # Steepness
            x0 = 0.5  # Center point
            return 1 / (1 + math.exp(-k * (x - x0)))
        else:
            # Linear characteristic as default
            return x
    
    def calculate_flow_rate(self, pressure_drop, fluid_type="water", temperature=20, 
                           glycol_percentage=0):
        """
        Calculate flow rate given a pressure drop
        
        Args:
            pressure_drop (float): Pressure drop in kPa
            fluid_type (str): Type of fluid
            temperature (float): Fluid temperature in °C
            glycol_percentage (int): Percentage of glycol in mixture
            
        Returns:
            float: Flow rate in m³/h
        """
        # Adjust Kv for valve opening
        effective_kv = self.kv * self.get_opening_characteristic(self.opening)
        
        # Get specific gravity of fluid
        _, density = self.get_fluid_properties(fluid_type, temperature, glycol_percentage)
        specific_gravity = density / 1000  # Relative to water
        
        # Convert pressure drop from kPa to bar
        pressure_drop_bar = pressure_drop / 100
        
        # Calculate flow rate using the Kv formula
        # Q = Kv * √(ΔP / SG)
        flow_rate = effective_kv * math.sqrt(pressure_drop_bar / specific_gravity)
        
        return flow_rate
    
    def calculate_cv(self):
        """
        Calculate valve flow coefficient in US units (Cv)
        
        Returns:
            float: Cv value (GPM/psi^0.5)
        """
        # Convert Kv to Cv
        # Cv = 1.156 * Kv
        return 1.156 * self.kv
    
    def set_valve_specs(self, kv=None, valve_type=None, valve_size=None, opening=None):
        """
        Set valve specifications
        
        Args:
            kv (float, optional): Flow coefficient in m³/h/bar^0.5
            valve_type (str, optional): Type of valve (globe, ball, butterfly)
            valve_size (int, optional): Valve size in mm
            opening (float, optional): Valve opening percentage (0-100)
        """
        if kv is not None:
            self.kv = kv
        if valve_type is not None:
            self.valve_type = valve_type
        if valve_size is not None:
            self.valve_size = valve_size
            # Update Kv based on size if not explicitly provided
            if kv is None:
                if valve_type == "globe":
                    self.kv = valve_size / 25 * 6.0
                elif valve_type == "ball":
                    self.kv = valve_size / 25 * 10.0
                elif valve_type == "butterfly":
                    self.kv = valve_size / 25 * 8.0
        if opening is not None:
            self.opening = max(min(opening, 100), 0) 