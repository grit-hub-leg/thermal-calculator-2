"""
Fan model for the Data Center Cooling Calculator.
"""

import math


class Fan:
    """
    Model for a fan used in active rear door cooling solutions.
    """
    
    def __init__(self):
        """Initialize the fan model"""
        # Default parameters
        self.max_flow_rate = 5000.0  # Maximum air flow rate in m³/h
        self.max_pressure = 100.0    # Maximum static pressure in Pa
        self.max_power = 0.2         # Maximum power consumption in kW
        self.efficiency = 0.7        # Fan efficiency (0-1)
        self.diameter = 200.0        # Fan diameter in mm
        self.quantity = 3            # Number of fans in the unit
        
    def calculate_flow_at_pressure(self, static_pressure, speed_percentage):
        """
        Calculate air flow rate at a given static pressure and fan speed
        
        Args:
            static_pressure (float): Static pressure in Pa
            speed_percentage (float): Fan speed as percentage of maximum (0-100)
            
        Returns:
            float: Air flow rate in m³/h
        """
        # Adjust for speed percentage
        speed_ratio = speed_percentage / 100.0
        
        # Calculate max pressure at current speed (proportional to square of speed)
        max_pressure_at_speed = self.max_pressure * (speed_ratio ** 2)
        
        # Check if pressure is too high for fan
        if static_pressure > max_pressure_at_speed:
            return 0.0  # Fan cannot overcome this pressure
        
        # Simple fan curve approximation
        flow_ratio = math.sqrt(1 - (static_pressure / max_pressure_at_speed))
        
        # Calculate flow rate
        flow_rate = self.max_flow_rate * speed_ratio * flow_ratio
        
        # Adjust for multiple fans
        flow_rate *= self.quantity
        
        return flow_rate
    
    def calculate_power(self, flow_rate, static_pressure, speed_percentage):
        """
        Calculate fan power consumption
        
        Args:
            flow_rate (float): Air flow rate in m³/h
            static_pressure (float): Static pressure in Pa
            speed_percentage (float): Fan speed as percentage of maximum (0-100)
            
        Returns:
            float: Power consumption in kW
        """
        # Convert units
        flow_rate_m3s = flow_rate / 3600  # m³/s
        
        # Adjust flow rate per fan
        flow_rate_per_fan = flow_rate_m3s / self.quantity
        
        # Calculate hydraulic power (P = Q × ΔP)
        hydraulic_power = flow_rate_per_fan * static_pressure  # Watts
        
        # Account for fan efficiency
        shaft_power = hydraulic_power / self.efficiency  # Watts
        
        # Convert to kW
        power_kw = shaft_power / 1000  # kW
        
        # Multiply by number of fans
        total_power = power_kw * self.quantity
        
        # Alternative calculation method based on speed percentage
        speed_ratio = speed_percentage / 100.0
        power_by_speed = self.max_power * (speed_ratio ** 3) * self.quantity
        
        # Use the maximum of the two methods for safety
        return max(total_power, power_by_speed)
    
    def calculate_speed_for_flow(self, required_flow, static_pressure):
        """
        Calculate required fan speed percentage for a specific flow rate
        
        Args:
            required_flow (float): Required air flow rate in m³/h
            static_pressure (float): Static pressure in Pa
            
        Returns:
            float: Required fan speed as percentage of maximum (0-100)
        """
        # Adjust flow rate for number of fans
        flow_per_fan = required_flow / self.quantity
        
        # Calculate flow ratio compared to maximum
        flow_ratio = flow_per_fan / self.max_flow_rate
        
        # Estimate speed percentage needed (iterative approach)
        min_speed = 0.0
        max_speed = 100.0
        speed = 50.0
        tolerance = 0.01
        
        for _ in range(10):  # Maximum 10 iterations
            current_flow = self.calculate_flow_at_pressure(static_pressure, speed) / self.quantity
            
            if abs(current_flow - flow_per_fan) < tolerance:
                break
            
            if current_flow < flow_per_fan:
                min_speed = speed
                speed = (speed + max_speed) / 2
            else:
                max_speed = speed
                speed = (speed + min_speed) / 2
        
        # Ensure the result is within valid range
        speed = max(min(speed, 100.0), 0.0)
        
        return speed
    
    def calculate_pressure_from_flow(self, flow_rate, speed_percentage):
        """
        Calculate static pressure given flow rate and fan speed
        
        Args:
            flow_rate (float): Air flow rate in m³/h
            speed_percentage (float): Fan speed as percentage of maximum (0-100)
            
        Returns:
            float: Static pressure in Pa
        """
        # Adjust for speed percentage
        speed_ratio = speed_percentage / 100.0
        
        # Calculate max pressure and flow at current speed
        max_pressure_at_speed = self.max_pressure * (speed_ratio ** 2)
        max_flow_at_speed = self.max_flow_rate * speed_ratio * self.quantity
        
        # Check if flow rate is too high for fan speed
        if flow_rate > max_flow_at_speed:
            return 0.0  # Fan cannot achieve this flow rate at given speed
        
        # Calculate flow ratio
        flow_ratio = flow_rate / max_flow_at_speed
        
        # Simple fan curve approximation
        static_pressure = max_pressure_at_speed * (1 - (flow_ratio ** 2))
        
        return static_pressure
    
    def set_fan_specs(self, max_flow_rate=None, max_pressure=None, max_power=None, 
                     efficiency=None, diameter=None, quantity=None):
        """
        Set fan specifications
        
        Args:
            max_flow_rate (float, optional): Maximum air flow rate in m³/h
            max_pressure (float, optional): Maximum static pressure in Pa
            max_power (float, optional): Maximum power consumption in kW
            efficiency (float, optional): Fan efficiency (0-1)
            diameter (float, optional): Fan diameter in mm
            quantity (int, optional): Number of fans in the unit
        """
        if max_flow_rate is not None:
            self.max_flow_rate = max_flow_rate
        if max_pressure is not None:
            self.max_pressure = max_pressure
        if max_power is not None:
            self.max_power = max_power
        if efficiency is not None:
            self.efficiency = efficiency
        if diameter is not None:
            self.diameter = diameter
        if quantity is not None:
            self.quantity = quantity 