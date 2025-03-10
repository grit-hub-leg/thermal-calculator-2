"""
Heat exchanger model for the Data Center Cooling Calculator.
"""

import math


class HeatExchanger:
    """
    Model for a liquid-to-air heat exchanger used in rear door cooling solutions.
    """
    
    def __init__(self):
        """Initialize the heat exchanger model"""
        # Default parameters
        self.effectiveness = 0.7  # Heat exchanger effectiveness (0-1)
        self.u_value = 30.0      # Overall heat transfer coefficient (W/m²·K)
        self.area = 1.5          # Heat transfer area (m²)
        self.rows = 3            # Number of tube rows
        self.fin_spacing = 2.0   # Fin spacing (mm)
        
    def calculate_heat_transfer(self, water_flow, water_temp_in, air_flow, air_temp_in):
        """
        Calculate heat transfer in the heat exchanger
        
        Args:
            water_flow (float): Water flow rate in m³/h
            water_temp_in (float): Water inlet temperature in °C
            air_flow (float): Air flow rate in m³/h
            air_temp_in (float): Air inlet temperature in °C
            
        Returns:
            dict: Heat transfer results
        """
        # Convert units
        water_flow_m3s = water_flow / 3600  # m³/s
        air_flow_m3s = air_flow / 3600      # m³/s
        
        # Properties of fluids
        water_density = 1000.0  # kg/m³
        water_specific_heat = 4.18  # kJ/kg·K
        air_density = 1.2  # kg/m³
        air_specific_heat = 1.005  # kJ/kg·K
        
        # Calculate mass flow rates
        water_mass_flow = water_flow_m3s * water_density  # kg/s
        air_mass_flow = air_flow_m3s * air_density        # kg/s
        
        # Calculate heat capacity rates
        water_heat_capacity_rate = water_mass_flow * water_specific_heat  # kW/K
        air_heat_capacity_rate = air_mass_flow * air_specific_heat        # kW/K
        
        # Determine minimum and maximum heat capacity rates
        c_min = min(water_heat_capacity_rate, air_heat_capacity_rate)
        c_max = max(water_heat_capacity_rate, air_heat_capacity_rate)
        
        # Calculate heat exchanger effectiveness
        ntu = self.u_value * self.area / c_min
        c_ratio = c_min / c_max
        
        # Use NTU method to calculate effectiveness for a cross-flow heat exchanger
        if c_ratio < 0.01:  # One fluid with constant temperature (C_max -> infinity)
            effectiveness = 1 - math.exp(-ntu)
        else:
            # Cross-flow with both fluids unmixed
            effectiveness = 1 - math.exp(
                (1 / c_ratio) * (ntu ** 0.22) * (math.exp(-c_ratio * (ntu ** 0.78)) - 1)
            )
        
        # Apply correction factors
        effectiveness *= self.effectiveness / 0.7  # Adjust based on reference effectiveness
        
        # Calculate maximum possible heat transfer
        q_max = c_min * (air_temp_in - water_temp_in)  # kW
        
        # Calculate actual heat transfer
        q_actual = effectiveness * q_max  # kW
        
        # Calculate outlet temperatures
        water_temp_out = water_temp_in + q_actual / water_heat_capacity_rate
        air_temp_out = air_temp_in - q_actual / air_heat_capacity_rate
        
        # Calculate log mean temperature difference (LMTD)
        delta_t1 = air_temp_in - water_temp_out
        delta_t2 = air_temp_out - water_temp_in
        if abs(delta_t1 - delta_t2) < 0.1:
            lmtd = delta_t1  # Avoid division by near-zero
        else:
            lmtd = (delta_t1 - delta_t2) / math.log(delta_t1 / delta_t2)
        
        # Calculate UA value (overall heat transfer coefficient times area)
        ua_value = q_actual / lmtd
        
        return {
            "heat_transfer": q_actual,
            "effectiveness": effectiveness,
            "water_outlet_temp": water_temp_out,
            "air_outlet_temp": air_temp_out,
            "lmtd": lmtd,
            "ua_value": ua_value
        }
    
    def calculate_pressure_drop(self, water_flow):
        """
        Calculate water-side pressure drop through the heat exchanger
        
        Args:
            water_flow (float): Water flow rate in m³/h
            
        Returns:
            float: Pressure drop in kPa
        """
        # Converting to SI units
        water_flow_m3s = water_flow / 3600  # m³/s
        
        # Reference conditions
        reference_flow = 2.0 / 3600  # m³/s (2.0 m³/h)
        reference_pressure_drop = 20.0  # kPa
        
        # Pressure drop is proportional to square of flow rate
        pressure_drop = reference_pressure_drop * (water_flow_m3s / reference_flow) ** 2
        
        # Apply correction for number of rows (more rows = more pressure drop)
        pressure_drop *= self.rows / 3.0
        
        # Apply correction for fin spacing (smaller spacing = more pressure drop)
        pressure_drop *= 2.0 / self.fin_spacing
        
        return pressure_drop
    
    def calculate_air_pressure_drop(self, air_flow):
        """
        Calculate air-side pressure drop through the heat exchanger
        
        Args:
            air_flow (float): Air flow rate in m³/h
            
        Returns:
            float: Pressure drop in Pa
        """
        # Converting to SI units
        air_flow_m3s = air_flow / 3600  # m³/s
        
        # Reference conditions
        reference_flow = 5000.0 / 3600  # m³/s (5000 m³/h)
        reference_pressure_drop = 50.0  # Pa
        
        # Pressure drop is proportional to square of flow rate
        pressure_drop = reference_pressure_drop * (air_flow_m3s / reference_flow) ** 2
        
        # Apply correction for number of rows
        pressure_drop *= self.rows / 3.0
        
        # Apply correction for fin spacing
        pressure_drop *= 2.0 / self.fin_spacing
        
        return pressure_drop
    
    def set_geometry(self, area=None, rows=None, fin_spacing=None):
        """
        Set heat exchanger geometry
        
        Args:
            area (float, optional): Heat transfer area in m²
            rows (int, optional): Number of tube rows
            fin_spacing (float, optional): Fin spacing in mm
        """
        if area is not None:
            self.area = area
        if rows is not None:
            self.rows = rows
        if fin_spacing is not None:
            self.fin_spacing = fin_spacing
    
    def set_performance(self, effectiveness=None, u_value=None):
        """
        Set heat exchanger performance parameters
        
        Args:
            effectiveness (float, optional): Heat exchanger effectiveness (0-1)
            u_value (float, optional): Overall heat transfer coefficient (W/m²·K)
        """
        if effectiveness is not None:
            self.effectiveness = effectiveness
        if u_value is not None:
            self.u_value = u_value 