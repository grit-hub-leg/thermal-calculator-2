"""
Piping model for the Data Center Cooling Calculator.
"""

import math


class Piping:
    """
    Model for piping components in cooling systems.
    """
    
    def __init__(self):
        """Initialize the piping model"""
        # Default parameters
        self.pipe_diameter = 25.0  # Pipe internal diameter in mm
        self.pipe_length = 10.0    # Pipe length in m
        self.pipe_material = "copper"
        self.roughness = 0.0015    # Pipe roughness in mm
        self.fittings = {
            "elbows": 4,           # Number of 90° elbows
            "tees": 2,             # Number of tees
            "valves": 2            # Number of valves
        }
        
    def calculate_pressure_drop(self, flow_rate, fluid_type="water", temperature=20, 
                                glycol_percentage=0):
        """
        Calculate pressure drop through the piping system
        
        Args:
            flow_rate (float): Water flow rate in m³/h
            fluid_type (str): Type of fluid (water, propylene_glycol, ethylene_glycol)
            temperature (float): Fluid temperature in °C
            glycol_percentage (int): Percentage of glycol in mixture
            
        Returns:
            float: Pressure drop in kPa
        """
        # Convert units
        flow_rate_m3s = flow_rate / 3600  # m³/s
        diameter_m = self.pipe_diameter / 1000  # m
        
        # Get fluid properties
        density, viscosity = self.get_fluid_properties(fluid_type, temperature, glycol_percentage)
        
        # Calculate flow velocity
        area = math.pi * (diameter_m ** 2) / 4  # m²
        velocity = flow_rate_m3s / area  # m/s
        
        # Calculate Reynolds number
        reynolds = density * velocity * diameter_m / viscosity
        
        # Calculate friction factor using Colebrook equation
        relative_roughness = (self.roughness / 1000) / diameter_m
        
        if reynolds < 2000:
            # Laminar flow
            friction_factor = 64 / reynolds
        elif reynolds > 4000:
            # Turbulent flow - use approximation of Colebrook equation
            a = -2 * math.log10(relative_roughness / 3.7 + 2.51 / (reynolds * math.sqrt(0.02)))
            b = -2 * math.log10(relative_roughness / 3.7 + 2.51 / (reynolds * math.sqrt(0.018)))
            friction_factor = (0.02 - 0.018) / (a - b) * (a - 1/math.sqrt(0.02)) + 0.02
        else:
            # Transitional flow - interpolate
            laminar_factor = 64 / 2000
            a = -2 * math.log10(relative_roughness / 3.7 + 2.51 / (4000 * math.sqrt(0.02)))
            b = -2 * math.log10(relative_roughness / 3.7 + 2.51 / (4000 * math.sqrt(0.018)))
            turbulent_factor = (0.02 - 0.018) / (a - b) * (a - 1/math.sqrt(0.02)) + 0.02
            
            # Linear interpolation
            t = (reynolds - 2000) / 2000
            friction_factor = laminar_factor * (1 - t) + turbulent_factor * t
        
        # Calculate straight pipe pressure drop using Darcy-Weisbach equation
        # ΔP = f * (L/D) * (ρv²/2)
        straight_pressure_drop = (friction_factor * self.pipe_length / diameter_m * 
                                 density * (velocity ** 2) / 2)
        
        # Calculate equivalent length of fittings
        eq_length = self.calculate_equivalent_length()
        
        # Calculate fitting pressure drop
        fitting_pressure_drop = (friction_factor * eq_length / diameter_m * 
                                density * (velocity ** 2) / 2)
        
        # Total pressure drop in Pa
        total_pressure_drop = straight_pressure_drop + fitting_pressure_drop
        
        # Convert to kPa
        return total_pressure_drop / 1000
    
    def get_fluid_properties(self, fluid_type, temperature, glycol_percentage):
        """
        Get fluid density and viscosity
        
        Args:
            fluid_type (str): Type of fluid
            temperature (float): Fluid temperature in °C
            glycol_percentage (int): Percentage of glycol in mixture
            
        Returns:
            tuple: (density in kg/m³, viscosity in Pa·s)
        """
        if fluid_type == "water":
            # Approximate water properties as a function of temperature
            density = 1000 - 0.1 * (temperature - 20)  # kg/m³
            viscosity = 0.001 * math.exp(-0.02 * (temperature - 20))  # Pa·s
        elif fluid_type == "propylene_glycol":
            # Approximate propylene glycol mixture properties
            base_density = 1000 - 0.1 * (temperature - 20)  # kg/m³
            density = base_density + glycol_percentage * 1.5
            
            base_viscosity = 0.001 * math.exp(-0.02 * (temperature - 20))  # Pa·s
            glycol_factor = 1 + 0.1 * glycol_percentage  # viscosity increases with glycol percentage
            temp_factor = math.exp(-0.03 * temperature)  # viscosity decreases with temperature
            viscosity = base_viscosity * glycol_factor * temp_factor
        elif fluid_type == "ethylene_glycol":
            # Approximate ethylene glycol mixture properties
            base_density = 1000 - 0.1 * (temperature - 20)  # kg/m³
            density = base_density + glycol_percentage * 1.8
            
            base_viscosity = 0.001 * math.exp(-0.02 * (temperature - 20))  # Pa·s
            glycol_factor = 1 + 0.08 * glycol_percentage  # viscosity increases with glycol percentage
            temp_factor = math.exp(-0.025 * temperature)  # viscosity decreases with temperature
            viscosity = base_viscosity * glycol_factor * temp_factor
        else:
            # Default to water properties
            density = 1000  # kg/m³
            viscosity = 0.001  # Pa·s
        
        return density, viscosity
    
    def calculate_equivalent_length(self):
        """
        Calculate equivalent length of all fittings
        
        Returns:
            float: Equivalent length in m
        """
        # Typical equivalent length ratios (L/D)
        elbow_ratio = 30
        tee_ratio = 60
        valve_ratio = 150
        
        # Calculate total equivalent length
        diameter_m = self.pipe_diameter / 1000  # m
        eq_length = (self.fittings["elbows"] * elbow_ratio + 
                     self.fittings["tees"] * tee_ratio + 
                     self.fittings["valves"] * valve_ratio) * diameter_m
        
        return eq_length
    
    def calculate_heat_loss(self, fluid_temp, ambient_temp, insulation_thickness=20):
        """
        Calculate heat loss through piping
        
        Args:
            fluid_temp (float): Fluid temperature in °C
            ambient_temp (float): Ambient temperature in °C
            insulation_thickness (float): Insulation thickness in mm
            
        Returns:
            float: Heat loss in kW
        """
        # Convert to meters
        diameter_m = self.pipe_diameter / 1000
        insulation_thickness_m = insulation_thickness / 1000
        
        # Thermal conductivity of insulation (typical value for pipe insulation)
        k_insulation = 0.04  # W/(m·K)
        
        # Heat transfer coefficient for outer surface to air
        h_outer = 10  # W/(m²·K)
        
        # Outer diameter of insulated pipe
        outer_diameter = diameter_m + 2 * insulation_thickness_m
        
        # Calculate thermal resistance
        r1 = diameter_m / 2
        r2 = r1 + insulation_thickness_m
        
        # Thermal resistance of insulation
        r_insulation = math.log(r2/r1) / (2 * math.pi * k_insulation)
        
        # Thermal resistance of outer surface
        r_surface = 1 / (2 * math.pi * r2 * h_outer)
        
        # Total thermal resistance per unit length
        r_total = r_insulation + r_surface
        
        # Heat loss per unit length
        q_per_length = (fluid_temp - ambient_temp) / r_total  # W/m
        
        # Total heat loss
        q_total = q_per_length * self.pipe_length  # W
        
        # Convert to kW
        q_total_kw = q_total / 1000
        
        return q_total_kw
    
    def set_piping_specs(self, pipe_diameter=None, pipe_length=None, 
                         pipe_material=None, roughness=None, fittings=None):
        """
        Set piping specifications
        
        Args:
            pipe_diameter (float, optional): Pipe internal diameter in mm
            pipe_length (float, optional): Pipe length in m
            pipe_material (str, optional): Pipe material
            roughness (float, optional): Pipe roughness in mm
            fittings (dict, optional): Dictionary of fittings counts
        """
        if pipe_diameter is not None:
            self.pipe_diameter = pipe_diameter
        if pipe_length is not None:
            self.pipe_length = pipe_length
        if pipe_material is not None:
            self.pipe_material = pipe_material
            # Update roughness based on material
            if roughness is None:
                if pipe_material == "copper":
                    self.roughness = 0.0015
                elif pipe_material == "steel":
                    self.roughness = 0.045
                elif pipe_material == "pvc":
                    self.roughness = 0.0015
        if roughness is not None:
            self.roughness = roughness
        if fittings is not None:
            self.fittings.update(fittings) 