import math
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class InputParameters:
    """Input parameters for thermal calculations."""
    heat_load: float = 100.0  # kW - Total heat output from servers
    ambient_temp: float = 25.0  # °C - Ambient temperature
    height: float = 10.0  # m - Height of thermosiphon system
    cold_pipe_diameter: float = 0.3  # m - Cold pipe diameter
    hot_pipe_diameter: float = 0.3  # m - Hot pipe diameter
    cold_temp: float = 35.0  # °C - Cold water temperature
    hot_temp: float = 45.0  # °C - Hot water temperature
    heat_pipe_count: int = 100  # Count of heat pipes
    heat_pipe_diameter: float = 10.0  # mm - Heat pipe diameter
    pcm_volume: float = 0.5  # m³ - Phase change material volume
    ahu_surface_area: float = 40.0  # m² - AHU surface area
    dimple_density: float = 1000.0  # dimples/m² - Dimples per square meter


class ThermosiphonCalculator:
    """Calculates thermosiphon performance metrics."""
    
    def __init__(self, params: InputParameters):
        self.params = params
        # Constants
        self.water_density = 997  # kg/m³
        self.specific_heat = 4186  # J/kg·K
        self.thermal_expansion = 0.0002  # K⁻¹
        self.gravity = 9.81  # m/s²
        self.friction_factor = 0.02  # Pipe friction factor
        self.minor_loss = 5  # Sum of minor loss coefficients
        
    def calculate(self):
        """Perform thermosiphon calculations."""
        # Basic parameters
        temp_diff = self.params.hot_temp - self.params.cold_temp  # K
        cold_pipe_area = math.pi * (self.params.cold_pipe_diameter/2)**2  # m²
        hot_pipe_area = math.pi * (self.params.hot_pipe_diameter/2)**2  # m²
        pipe_length = self.params.height * 2.5  # m - Total pipe length
        
        # Thermosiphon calculations
        density_change = self.water_density * self.thermal_expansion * temp_diff  # kg/m³
        driving_pressure = density_change * self.gravity * self.params.height  # Pa
        
        # Flow rate calculation
        flow_rate = math.sqrt(
            (2 * driving_pressure * self.water_density**2 * cold_pipe_area**2) /
            (self.water_density * (self.friction_factor * pipe_length + self.minor_loss))
        )  # kg/s
        
        volumetric_flow = flow_rate / self.water_density * 1000  # L/s
        flow_velocity = volumetric_flow / (1000 * cold_pipe_area)  # m/s
        
        # Heat transfer capacity
        heat_capacity = flow_rate * self.specific_heat * temp_diff / 1000  # kW
        system_efficiency = min(heat_capacity / self.params.heat_load * 100, 100)  # %
        
        return {
            "temp_diff": temp_diff,
            "density_change": density_change,
            "driving_pressure": driving_pressure,
            "flow_rate": flow_rate,
            "volumetric_flow": volumetric_flow,
            "flow_velocity": flow_velocity,
            "heat_capacity": heat_capacity,
            "system_efficiency": system_efficiency
        }


class HeatPipeCalculator:
    """Calculates heat pipe performance metrics."""
    
    def __init__(self, params: InputParameters):
        self.params = params
        self.figure_of_merit = 1790  # W/m² - Figure of merit for water
        self.heat_pipe_length = 0.5  # m - Heat pipe length
        self.interface_loss = 0.15  # Heat loss at stage interface
        
    def calculate(self):
        """Perform heat pipe calculations."""
        # Convert mm to m
        heat_pipe_diameter = self.params.heat_pipe_diameter / 1000  # m
        
        # Heat pipe capacity calculations
        heat_pipe_capacity = self.figure_of_merit * heat_pipe_diameter * self.heat_pipe_length  # W
        total_capacity = heat_pipe_capacity * self.params.heat_pipe_count / 1000  # kW
        
        # Two-stage calculations
        stage1_capacity = total_capacity  # kW
        stage2_capacity = stage1_capacity * (1 - self.interface_loss)  # kW
        
        # Effective properties
        effective_conductivity = 12000  # W/m·K
        copper_ratio = effective_conductivity / 400  # Ratio to copper
        
        system_efficiency = min(stage2_capacity / self.params.heat_load * 100, 100)  # %
        
        return {
            "heat_pipe_capacity": heat_pipe_capacity,
            "total_capacity": total_capacity,
            "stage1_capacity": stage1_capacity,
            "stage2_capacity": stage2_capacity,
            "effective_conductivity": effective_conductivity,
            "copper_ratio": copper_ratio,
            "system_efficiency": system_efficiency
        }


class PCMCalculator:
    """Calculates PCM performance metrics."""
    
    def __init__(self, params: InputParameters):
        self.params = params
        # PCM properties (CaCl₂·6H₂O)
        self.melting_point = 29  # °C
        self.latent_heat = 190  # kJ/kg
        self.pcm_density = 1600  # kg/m³
        self.specific_heat_solid = 1.4  # kJ/kg·K
        self.specific_heat_liquid = 2.1  # kJ/kg·K
        self.initial_temp = 25  # °C
        self.final_temp = 35  # °C
        
    def calculate(self):
        """Perform PCM calculations."""
        # Basic calculations
        pcm_mass = self.pcm_density * self.params.pcm_volume  # kg
        
        # Energy storage calculations
        sensible_heat_solid = pcm_mass * self.specific_heat_solid * (self.melting_point - self.initial_temp)  # kJ
        latent_heat_capacity = pcm_mass * self.latent_heat  # kJ
        sensible_heat_liquid = pcm_mass * self.specific_heat_liquid * (self.final_temp - self.melting_point)  # kJ
        
        total_energy = sensible_heat_solid + latent_heat_capacity + sensible_heat_liquid  # kJ
        storage_time = total_energy / (self.params.heat_load * 1000) * 60  # minutes
        energy_density = total_energy / (self.params.pcm_volume * 1000)  # kWh/m³
        
        return {
            "pcm_mass": pcm_mass,
            "sensible_heat_solid": sensible_heat_solid,
            "latent_heat_capacity": latent_heat_capacity,
            "sensible_heat_liquid": sensible_heat_liquid,
            "total_energy": total_energy,
            "storage_time": storage_time,
            "energy_density": energy_density
        }


class DimpledSurfaceCalculator:
    """Calculates dimpled surface performance metrics."""
    
    def __init__(self, params: InputParameters):
        self.params = params
        self.dimple_diameter = 0.01  # m
        self.dimple_depth = 0.005  # m
        self.surface_area_factor = 1.7  # Surface area enhancement factor
        self.base_heat_transfer = 15  # W/m²·K
        self.dimple_enhancement = 2.2  # Heat transfer enhancement factor
        
    def calculate(self):
        """Perform dimpled surface calculations."""
        # Basic calculations
        total_dimples = self.params.ahu_surface_area * self.params.dimple_density  # Total dimples
        enhanced_area = self.params.ahu_surface_area * self.surface_area_factor  # m²
        
        # Heat transfer calculations
        enhanced_coefficient = self.base_heat_transfer * self.dimple_enhancement  # W/m²·K
        
        temp_diff = self.params.cold_temp - self.params.ambient_temp  # K
        base_dissipation = self.params.ahu_surface_area * self.base_heat_transfer * temp_diff / 1000  # kW
        enhanced_dissipation = enhanced_area * enhanced_coefficient * temp_diff / 1000  # kW
        
        improvement = (enhanced_dissipation - base_dissipation) / base_dissipation * 100  # %
        
        return {
            "total_dimples": total_dimples,
            "enhanced_area": enhanced_area,
            "enhanced_coefficient": enhanced_coefficient,
            "temp_diff": temp_diff,
            "base_dissipation": base_dissipation,
            "enhanced_dissipation": enhanced_dissipation,
            "improvement": improvement
        }


class SystemPerformanceCalculator:
    """Calculates overall system performance metrics."""
    
    def __init__(self, params: InputParameters):
        self.params = params
        self.thermo_calc = ThermosiphonCalculator(params)
        self.heat_pipe_calc = HeatPipeCalculator(params)
        self.pcm_calc = PCMCalculator(params)
        self.dimple_calc = DimpledSurfaceCalculator(params)
        
        # Constants
        self.conventional_pue = 1.67  # Conventional cooling PUE
        self.passive_pue = 1.06  # Passive system PUE
        self.electricity_cost = 0.12  # $/kWh
        self.carbon_factor = 0.4  # tonnes CO₂/MWh
        self.system_cost = 60000  # $ - Estimated system cost
        
    def calculate(self):
        """Calculate system performance metrics."""
        # Get results from individual calculators
        thermo_results = self.thermo_calc.calculate()
        heat_pipe_results = self.heat_pipe_calc.calculate()
        pcm_results = self.pcm_calc.calculate()
        dimple_results = self.dimple_calc.calculate()
        
        # System capacity calculations
        thermosiphon_capacity = thermo_results["heat_capacity"]  # kW
        heat_pipe_capacity = heat_pipe_results["stage2_capacity"]  # kW
        pcm_buffer_capacity = pcm_results["total_energy"] / 3600  # kWh
        ahu_dissipation = dimple_results["enhanced_dissipation"]  # kW
        
        # Performance metrics
        thermal_coverage = min(min(thermosiphon_capacity, heat_pipe_capacity) / self.params.heat_load * 100, 100)  # %
        buffer_time = pcm_results["storage_time"]  # minutes
        
        # Energy and cost calculations
        energy_savings = (self.conventional_pue - self.passive_pue) / self.conventional_pue * self.params.heat_load * 24 * 365 / 1000  # MWh/year
        cost_savings = energy_savings * self.electricity_cost * 1000  # $/year
        co2_reduction = energy_savings * self.carbon_factor  # tonnes/year
        roi_period = self.system_cost / cost_savings  # years
        
        return {
            "thermosiphon_capacity": thermosiphon_capacity,
            "heat_pipe_capacity": heat_pipe_capacity,
            "pcm_buffer_capacity": pcm_buffer_capacity,
            "ahu_dissipation": ahu_dissipation,
            "thermal_coverage": thermal_coverage,
            "buffer_time": buffer_time,
            "energy_savings": energy_savings,
            "cost_savings": cost_savings,
            "co2_reduction": co2_reduction,
            "roi_period": roi_period
        }
        
    def validate_parameters(self):
        """Validate input parameters against recommended ranges."""
        validations = {}
        
        # Height validation
        validations["height"] = "OK" if self.params.height >= 5 else "TOO LOW"
        
        # Temperature differential validation
        temp_diff = self.params.hot_temp - self.params.cold_temp
        validations["temp_diff"] = "OK" if 5 <= temp_diff <= 20 else "CHECK RANGE"
        
        # Flow velocity validation
        flow_velocity = self.thermo_calc.calculate()["flow_velocity"]
        validations["flow_velocity"] = "OK" if 0.1 <= flow_velocity <= 2.0 else "CHECK RANGE"
        
        # Heat pipe count validation
        validations["heat_pipe_count"] = "OK" if 50 <= self.params.heat_pipe_count <= 200 else "CHECK RANGE"
        
        # PCM volume validation
        validations["pcm_volume"] = "OK" if 0.3 <= self.params.pcm_volume <= 2.0 else "CHECK RANGE"
        
        # Capacity coverage validation
        thermal_coverage = self.calculate()["thermal_coverage"]
        validations["capacity_coverage"] = "OK" if thermal_coverage >= 60 else "INSUFFICIENT"
        
        return validations


class PassiveCoolingCalculator:
    """Main calculator class for passive cooling system."""
    
    def __init__(self, params: InputParameters = None):
        """Initialize with default parameters if none provided."""
        if params is None:
            # Default parameters
            self.params = InputParameters(
                heat_load=100.0,  # kW
                ambient_temp=25.0,  # °C
                height=10.0,  # m
                cold_pipe_diameter=0.3,  # m
                hot_pipe_diameter=0.3,  # m
                cold_temp=35.0,  # °C
                hot_temp=45.0,  # °C
                heat_pipe_count=100,  # pipes
                heat_pipe_diameter=10.0,  # mm
                pcm_volume=0.5,  # m³
                ahu_surface_area=40.0,  # m²
                dimple_density=1000.0  # dimples/m²
            )
        else:
            self.params = params
            
        self.system_calc = SystemPerformanceCalculator(self.params)
        
    def calculate_all(self):
        """Calculate all metrics and return comprehensive results."""
        thermo_results = ThermosiphonCalculator(self.params).calculate()
        heat_pipe_results = HeatPipeCalculator(self.params).calculate()
        pcm_results = PCMCalculator(self.params).calculate()
        dimple_results = DimpledSurfaceCalculator(self.params).calculate()
        system_results = self.system_calc.calculate()
        validations = self.system_calc.validate_parameters()
        
        return {
            "input_parameters": self.params,
            "thermosiphon": thermo_results,
            "heat_pipes": heat_pipe_results,
            "pcm": pcm_results,
            "dimpled_surface": dimple_results,
            "system_performance": system_results,
            "validations": validations
        }
    
    def print_report(self):
        """Print a comprehensive report of all calculations."""
        results = self.calculate_all()
        
        print("\n===== PASSIVE COOLING SYSTEM REPORT =====\n")
        
        print("INPUT PARAMETERS:")
        for key, value in vars(self.params).items():
            print(f"  {key}: {value}")
        
        print("\nTHERMOSIPHON PERFORMANCE:")
        for key, value in results["thermosiphon"].items():
            print(f"  {key}: {value:.2f}")
        
        print("\nHEAT PIPE PERFORMANCE:")
        for key, value in results["heat_pipes"].items():
            print(f"  {key}: {value:.2f}")
        
        print("\nPCM PERFORMANCE:")
        for key, value in results["pcm"].items():
            print(f"  {key}: {value:.2f}")
        
        print("\nDIMPLED SURFACE PERFORMANCE:")
        for key, value in results["dimpled_surface"].items():
            print(f"  {key}: {value:.2f}")
        
        print("\nSYSTEM PERFORMANCE:")
        for key, value in results["system_performance"].items():
            print(f"  {key}: {value:.2f}")
        
        print("\nVALIDATION RESULTS:")
        for key, value in results["validations"].items():
            print(f"  {key}: {value}")
        
        print("\n============================================\n")
    
    def plot_performance(self):
        """Generate performance plots."""
        # Create figure with subplots
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        
        # Calculate with varying height
        heights = np.linspace(5, 15, 10)
        capacities = []
        efficiencies = []
        
        for height in heights:
            params_copy = InputParameters(**vars(self.params))
            params_copy.height = height
            calculator = SystemPerformanceCalculator(params_copy)
            results = calculator.calculate()
            capacities.append(results["thermosiphon_capacity"])
            efficiencies.append(results["thermal_coverage"])
        
        # Plot height vs capacity
        axs[0, 0].plot(heights, capacities, 'b-o')
        axs[0, 0].set_title('Thermosiphon Capacity vs Height')
        axs[0, 0].set_xlabel('Height (m)')
        axs[0, 0].set_ylabel('Capacity (kW)')
        axs[0, 0].grid(True)
        
        # Calculate with varying PCM volume
        volumes = np.linspace(0.2, 1.0, 10)
        buffer_times = []
        
        for volume in volumes:
            params_copy = InputParameters(**vars(self.params))
            params_copy.pcm_volume = volume
            calculator = PCMCalculator(params_copy)
            results = calculator.calculate()
            buffer_times.append(results["storage_time"])
        
        # Plot PCM volume vs buffer time
        axs[0, 1].plot(volumes, buffer_times, 'r-o')
        axs[0, 1].set_title('Buffer Time vs PCM Volume')
        axs[0, 1].set_xlabel('PCM Volume (m³)')
        axs[0, 1].set_ylabel('Buffer Time (minutes)')
        axs[0, 1].grid(True)
        
        # Calculate with varying heat pipe count
        pipe_counts = np.linspace(50, 200, 10)
        pipe_capacities = []
        
        for count in pipe_counts:
            params_copy = InputParameters(**vars(self.params))
            params_copy.heat_pipe_count = int(count)
            calculator = HeatPipeCalculator(params_copy)
            results = calculator.calculate()
            pipe_capacities.append(results["stage2_capacity"])
        
        # Plot heat pipe count vs capacity
        axs[1, 0].plot(pipe_counts, pipe_capacities, 'g-o')
        axs[1, 0].set_title('Heat Pipe Capacity vs Count')
        axs[1, 0].set_xlabel('Heat Pipe Count')
        axs[1, 0].set_ylabel('Capacity (kW)')
        axs[1, 0].grid(True)
        
        # Calculate ROI for different heat loads
        heat_loads = np.linspace(50, 150, 10)
        roi_periods = []
        
        for load in heat_loads:
            params_copy = InputParameters(**vars(self.params))
            params_copy.heat_load = load
            calculator = SystemPerformanceCalculator(params_copy)
            results = calculator.calculate()
            roi_periods.append(results["roi_period"])
        
        # Plot heat load vs ROI
        axs[1, 1].plot(heat_loads, roi_periods, 'm-o')
        axs[1, 1].set_title('ROI Period vs Heat Load')
        axs[1, 1].set_xlabel('Heat Load (kW)')
        axs[1, 1].set_ylabel('ROI Period (years)')
        axs[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig('passive_cooling_performance.png')
        plt.show()


def read_from_solid_edge(se_file_path=None):
    """
    Read parameters from Solid Edge through a CSV export or API.
    This is a placeholder for integration with Solid Edge.
    """
    # In a real implementation, this would use the Solid Edge API
    # or read from a CSV file exported from Solid Edge
    
    # For now, return default values
    return InputParameters(
        heat_load=100.0,  # kW
        ambient_temp=25.0,  # °C
        height=10.0,  # m
        cold_pipe_diameter=0.3,  # m
        hot_pipe_diameter=0.3,  # m
        cold_temp=35.0,  # °C
        hot_temp=45.0,  # °C
        heat_pipe_count=100,  # pipes
        heat_pipe_diameter=10.0,  # mm
        pcm_volume=0.5,  # m³
        ahu_surface_area=40.0,  # m²
        dimple_density=1000.0  # dimples/m²
    )


def write_to_solid_edge(results, se_file_path=None):
    """
    Write calculation results back to Solid Edge through a CSV import or API.
    This is a placeholder for integration with Solid Edge.
    """
    # In a real implementation, this would use the Solid Edge API
    # or write to a CSV file to be imported into Solid Edge
    
    print("Results would be written to Solid Edge...")
    print(f"File path: {se_file_path}")
    print("Key performance metrics:")
    print(f"  Thermosiphon capacity: {results['system_performance']['thermosiphon_capacity']:.2f} kW")
    print(f"  Heat pipe capacity: {results['system_performance']['heat_pipe_capacity']:.2f} kW")
    print(f"  Thermal coverage: {results['system_performance']['thermal_coverage']:.2f}%")
    print(f"  ROI period: {results['system_performance']['roi_period']:.2f} years")


if __name__ == "__main__":
    # Example usage
    print("Passive Cooling System Calculator")
    print("--------------------------------")
    
    # Create calculator with default parameters
    calculator = PassiveCoolingCalculator()
    
    # Option to read from Solid Edge
    # params = read_from_solid_edge("path/to/model.par")
    # calculator = PassiveCoolingCalculator(params)
    
    # Calculate and print report
    calculator.print_report()
    
    # Generate performance plots
    calculator.plot_performance()
    
    # Option to write results back to Solid Edge
    # results = calculator.calculate_all()
    # write_to_solid_edge(results, "path/to/model.par")

