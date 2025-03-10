import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import json
import os
import sys
from dataclasses import dataclass, asdict

# Import the calculation module (assuming it's saved as thermal_calculator.py)
# If not, copy the previous Python code into thermal_calculator.py
try:
    from thermal_calculator import (InputParameters, ThermosiphonCalculator, 
                                  HeatPipeCalculator, PCMCalculator,
                                  DimpledSurfaceCalculator, SystemPerformanceCalculator,
                                  PassiveCoolingCalculator, read_from_solid_edge,
                                  write_to_solid_edge)
except ImportError:
    # Create a simple mock version for display purposes
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

    class PassiveCoolingCalculator:
        def __init__(self, params=None):
            self.params = params or InputParameters()
            
        def calculate_all(self):
            # Mock calculation results
            return {
                "input_parameters": self.params,
                "thermosiphon": {
                    "temp_diff": 10.0,
                    "density_change": 2.0,
                    "driving_pressure": 196.2,
                    "flow_rate": 14.33,
                    "volumetric_flow": 14.37,
                    "flow_velocity": 0.2,
                    "heat_capacity": 60.0,
                    "system_efficiency": 60.0
                },
                "heat_pipes": {
                    "heat_pipe_capacity": 8.95,
                    "total_capacity": 895.0,
                    "stage1_capacity": 65.0,
                    "stage2_capacity": 55.25,
                    "effective_conductivity": 12000.0,
                    "copper_ratio": 30.0,
                    "system_efficiency": 55.25
                },
                "pcm": {
                    "pcm_mass": 800.0,
                    "sensible_heat_solid": 4480.0,
                    "latent_heat_capacity": 152000.0,
                    "sensible_heat_liquid": 10080.0,
                    "total_energy": 166560.0,
                    "storage_time": 99.93,
                    "energy_density": 92.53
                },
                "dimpled_surface": {
                    "total_dimples": 40000.0,
                    "enhanced_area": 68.0,
                    "enhanced_coefficient": 33.0,
                    "temp_diff": 10.0,
                    "base_dissipation": 6.0,
                    "enhanced_dissipation": 22.44,
                    "improvement": 274.0
                },
                "system_performance": {
                    "thermosiphon_capacity": 60.0,
                    "heat_pipe_capacity": 55.25,
                    "pcm_buffer_capacity": 46.27,
                    "ahu_dissipation": 22.44,
                    "thermal_coverage": 55.25,
                    "buffer_time": 99.93,
                    "energy_savings": 225.257,
                    "cost_savings": 27030.84,
                    "co2_reduction": 90.1,
                    "roi_period": 2.22
                },
                "validations": {
                    "height": "OK",
                    "temp_diff": "OK",
                    "flow_velocity": "OK",
                    "heat_pipe_count": "OK",
                    "pcm_volume": "OK",
                    "capacity_coverage": "CHECK RANGE"
                }
            }
        
        def plot_performance(self):
            # Create a figure with subplots
            fig = plt.figure(figsize=(12, 10))
            return fig


class RearDoorCalculator:
    """Calculator for Rear Door Heat Exchanger performance."""
    
    def __init__(self, params=None):
        """Initialize with default parameters if none provided."""
        # Default RDHx parameters
        self.params = params or {
            "server_heat_load": 60.0,  # kW per rack
            "inlet_water_temp": 18.0,  # °C
            "outlet_water_temp": 28.0,  # °C
            "inlet_air_temp": 50.0,  # °C
            "outlet_air_temp": 22.0,  # °C
            "water_flow_rate": 5.0,  # L/s
            "air_flow_rate": 6847.0,  # m³/h
            "fan_count": 6,  # Number of fans
            "coil_rows": 6,  # Number of coil rows
            "door_width": 0.6,  # m
            "door_height": 2.0,  # m
        }
    
    def calculate(self):
        """Calculate rear door heat exchanger performance."""
        p = self.params
        
        # Convert units
        water_flow_m3s = p["water_flow_rate"] / 1000  # L/s to m³/s
        air_flow_m3s = p["air_flow_rate"] / 3600  # m³/h to m³/s
        
        # Water properties
        water_density = 997  # kg/m³
        water_cp = 4186  # J/kg·K
        
        # Air properties
        air_density = 1.2  # kg/m³
        air_cp = 1005  # J/kg·K
        
        # Calculate heat transfer based on water side
        water_mass_flow = water_flow_m3s * water_density  # kg/s
        water_delta_t = p["outlet_water_temp"] - p["inlet_water_temp"]  # K
        water_heat_capacity = water_mass_flow * water_cp * water_delta_t / 1000  # kW
        
        # Calculate heat transfer based on air side
        air_mass_flow = air_flow_m3s * air_density  # kg/s
        air_delta_t = p["inlet_air_temp"] - p["outlet_air_temp"]  # K
        air_heat_capacity = air_mass_flow * air_cp * air_delta_t / 1000  # kW
        
        # Calculate heat transfer effectiveness
        max_delta_t = p["inlet_air_temp"] - p["inlet_water_temp"]  # K
        effectiveness = water_delta_t / max_delta_t * 100  # %
        
        # Calculate heat transfer coefficient
        door_area = p["door_width"] * p["door_height"]  # m²
        log_mean_temp_diff = ((p["inlet_air_temp"] - p["outlet_water_temp"]) - 
                             (p["outlet_air_temp"] - p["inlet_water_temp"])) / \
                             np.log((p["inlet_air_temp"] - p["outlet_water_temp"]) / 
                                   (p["outlet_air_temp"] - p["inlet_water_temp"]))
        heat_transfer_coef = water_heat_capacity * 1000 / (door_area * log_mean_temp_diff)  # W/m²·K
        
        # Calculate passive mode performance (no fans)
        passive_air_flow = air_flow_m3s * 0.3  # Assume 30% flow without fans
        passive_air_mass_flow = passive_air_flow * air_density
        passive_delta_t = p["inlet_air_temp"] - (p["inlet_air_temp"] - 15)  # Assume less effective cooling
        passive_capacity = passive_air_mass_flow * air_cp * passive_delta_t / 1000  # kW
        passive_percentage = passive_capacity / p["server_heat_load"] * 100  # %
        
        return {
            "water_heat_capacity": water_heat_capacity,
            "air_heat_capacity": air_heat_capacity,
            "effectiveness": effectiveness,
            "heat_transfer_coefficient": heat_transfer_coef,
            "passive_cooling_capacity": passive_capacity,
            "passive_percentage": passive_percentage,
            "thermal_coverage": min(water_heat_capacity / p["server_heat_load"] * 100, 100),
            "water_velocity": water_flow_m3s / (0.01 * 0.5),  # Assume 1cm x 50cm pipe cross-section
            "air_velocity": air_flow_m3s / (p["door_width"] * p["door_height"]),
            "fan_power": p["fan_count"] * 0.12  # Assume 120W per fan
        }


class ThermalCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Thermal System Calculator")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Set style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # or 'alt', 'default', 'classic'
        
        # Define colors
        self.primary_color = "#0d6efd"
        self.secondary_color = "#6c757d"
        self.success_color = "#198754"
        self.info_color = "#0dcaf0"
        self.warning_color = "#ffc107"
        self.danger_color = "#dc3545"
        
        # Configure styles
        self.style.configure('Primary.TButton', background=self.primary_color, foreground='white')
        self.style.configure('Success.TButton', background=self.success_color, foreground='white')
        self.style.configure('Info.TLabel', background=self.info_color, foreground='white')
        
        # Set up notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.main_tab = ttk.Frame(self.notebook)
        self.thermosiphon_tab = ttk.Frame(self.notebook)
        self.heat_pipe_tab = ttk.Frame(self.notebook)
        self.pcm_tab = ttk.Frame(self.notebook)
        self.dimple_tab = ttk.Frame(self.notebook)
        self.rdh_tab = ttk.Frame(self.notebook)
        self.results_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text="Main Parameters")
        self.notebook.add(self.thermosiphon_tab, text="Thermosiphon")
        self.notebook.add(self.heat_pipe_tab, text="Heat Pipes")
        self.notebook.add(self.pcm_tab, text="PCM Storage")
        self.notebook.add(self.dimple_tab, text="Dimpled Surface")
        self.notebook.add(self.rdh_tab, text="Rear Door HX")
        self.notebook.add(self.results_tab, text="Results")
        
        # Initialize default parameters
        self.params = InputParameters(
    heat_load=100.0,
    ambient_temp=25.0,
    height=10.0,
    cold_pipe_diameter=0.3,
    hot_pipe_diameter=0.3,
    cold_temp=35.0,
    hot_temp=45.0,
    heat_pipe_count=100,
    heat_pipe_diameter=10.0,
    pcm_volume=0.5,
    ahu_surface_area=40.0,
    dimple_density=1000.0
)
        self.rdh_params = RearDoorCalculator().params
        
        # Set up tab contents
        self.setup_main_tab()
        self.setup_thermosiphon_tab()
        self.setup_heat_pipe_tab()
        self.setup_pcm_tab()
        self.setup_dimple_tab()
        self.setup_rdh_tab()
        self.setup_results_tab()
        
        # Create the calculator object
        self.calculator = PassiveCoolingCalculator(self.params)
        self.rdh_calculator = RearDoorCalculator(self.rdh_params)
        
        # Set up menu
        self.setup_menu()
        
        # Calculate initial results
        self.calculate()
    
    def setup_menu(self):
        """Set up the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_project)
        file_menu.add_command(label="Open...", command=self.open_project)
        file_menu.add_command(label="Save", command=self.save_project)
        file_menu.add_command(label="Save As...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Import from Solid Edge...", command=self.import_from_solid_edge)
        file_menu.add_command(label="Export to Solid Edge...", command=self.export_to_solid_edge)
        file_menu.add_separator()
        file_menu.add_command(label="Export Report...", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Calculate menu
        calc_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Calculate", menu=calc_menu)
        calc_menu.add_command(label="Run All Calculations", command=self.calculate)
        calc_menu.add_command(label="Parameter Validation", command=self.validate_parameters)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Sensitivity Analysis...", command=self.sensitivity_analysis)
        tools_menu.add_command(label="Optimization...", command=self.optimization)
        tools_menu.add_command(label="Generate Reports...", command=self.generate_reports)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_main_tab(self):
        """Set up the main parameters tab."""
        frame = ttk.Frame(self.main_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Passive Cooling System Parameters", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        # Create input fields
        row = 1
        
        # Heat Load
        ttk.Label(frame, text="Server Heat Load (kW):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.heat_load_var = tk.DoubleVar(value=self.params.heat_load)
        heat_load_entry = ttk.Entry(frame, textvariable=self.heat_load_var, width=10)
        heat_load_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # Ambient Temperature
        ttk.Label(frame, text="Ambient Temperature (°C):").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.ambient_temp_var = tk.DoubleVar(value=self.params.ambient_temp)
        ambient_temp_entry = ttk.Entry(frame, textvariable=self.ambient_temp_var, width=10)
        ambient_temp_entry.grid(row=row, column=3, sticky=tk.W, pady=5)
        
        row += 1
        
        # Height
        ttk.Label(frame, text="Height Differential (m):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.height_var = tk.DoubleVar(value=self.params.height)
        height_entry = ttk.Entry(frame, textvariable=self.height_var, width=10)
        height_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # Cold Pipe Diameter
        ttk.Label(frame, text="Cold Pipe Diameter (m):").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.cold_pipe_diameter_var = tk.DoubleVar(value=self.params.cold_pipe_diameter)
        cold_pipe_diameter_entry = ttk.Entry(frame, textvariable=self.cold_pipe_diameter_var, width=10)
        cold_pipe_diameter_entry.grid(row=row, column=3, sticky=tk.W, pady=5)
        
        row += 1
        
        # Hot Pipe Diameter
        ttk.Label(frame, text="Hot Pipe Diameter (m):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.hot_pipe_diameter_var = tk.DoubleVar(value=self.params.hot_pipe_diameter)
        hot_pipe_diameter_entry = ttk.Entry(frame, textvariable=self.hot_pipe_diameter_var, width=10)
        hot_pipe_diameter_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # Cold Water Temperature
        ttk.Label(frame, text="Cold Water Temperature (°C):").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.cold_temp_var = tk.DoubleVar(value=self.params.cold_temp)
        cold_temp_entry = ttk.Entry(frame, textvariable=self.cold_temp_var, width=10)
        cold_temp_entry.grid(row=row, column=3, sticky=tk.W, pady=5)
        
        row += 1
        
        # Hot Water Temperature
        ttk.Label(frame, text="Hot Water Temperature (°C):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.hot_temp_var = tk.DoubleVar(value=self.params.hot_temp)
        hot_temp_entry = ttk.Entry(frame, textvariable=self.hot_temp_var, width=10)
        hot_temp_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # Heat Pipe Count
        ttk.Label(frame, text="Heat Pipe Count:").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.heat_pipe_count_var = tk.IntVar(value=self.params.heat_pipe_count)
        heat_pipe_count_entry = ttk.Entry(frame, textvariable=self.heat_pipe_count_var, width=10)
        heat_pipe_count_entry.grid(row=row, column=3, sticky=tk.W, pady=5)
        
        row += 1
        
        # Heat Pipe Diameter
        ttk.Label(frame, text="Heat Pipe Diameter (mm):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.heat_pipe_diameter_var = tk.DoubleVar(value=self.params.heat_pipe_diameter)
        heat_pipe_diameter_entry = ttk.Entry(frame, textvariable=self.heat_pipe_diameter_var, width=10)
        heat_pipe_diameter_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # PCM Volume
        ttk.Label(frame, text="PCM Volume (m³):").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.pcm_volume_var = tk.DoubleVar(value=self.params.pcm_volume)
        pcm_volume_entry = ttk.Entry(frame, textvariable=self.pcm_volume_var, width=10)
        pcm_volume_entry.grid(row=row, column=3, sticky=tk.W, pady=5)
        
        row += 1
        
        # AHU Surface Area
        ttk.Label(frame, text="AHU Surface Area (m²):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.ahu_surface_area_var = tk.DoubleVar(value=self.params.ahu_surface_area)
        ahu_surface_area_entry = ttk.Entry(frame, textvariable=self.ahu_surface_area_var, width=10)
        ahu_surface_area_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # Dimple Density
        ttk.Label(frame, text="Dimple Density (dimples/m²):").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.dimple_density_var = tk.DoubleVar(value=self.params.dimple_density)
        dimple_density_entry = ttk.Entry(frame, textvariable=self.dimple_density_var, width=10)
        dimple_density_entry.grid(row=row, column=3, sticky=tk.W, pady=5)
        
        row += 1
        
        # Add some space
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=20)
        
        row += 1
        
        # Summary frame
        summary_frame = ttk.LabelFrame(frame, text="System Summary")
        summary_frame.grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=5)
        
        # Summary labels
        self.coverage_label = ttk.Label(summary_frame, text="Thermal Coverage: --")
        self.coverage_label.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        
        self.buffer_label = ttk.Label(summary_frame, text="Buffer Time: --")
        self.buffer_label.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.roi_label = ttk.Label(summary_frame, text="ROI Period: --")
        self.roi_label.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        
        self.efficiency_label = ttk.Label(summary_frame, text="System Efficiency: --")
        self.efficiency_label.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        row += 1
        
        # Buttons frame
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=4, pady=20)
        
        calculate_button = ttk.Button(button_frame, text="Calculate", command=self.calculate, style='Primary.TButton')
        calculate_button.pack(side=tk.LEFT, padx=5)
        
        validate_button = ttk.Button(button_frame, text="Validate Parameters", command=self.validate_parameters)
        validate_button.pack(side=tk.LEFT, padx=5)
        
        reset_button = ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_parameters)
        reset_button.pack(side=tk.LEFT, padx=5)
    
    def setup_thermosiphon_tab(self):
        """Set up the thermosiphon tab."""
        frame = ttk.Frame(self.thermosiphon_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Thermosiphon System Analysis", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        # Split into two columns
        left_frame = ttk.Frame(frame)
        left_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        
        right_frame = ttk.Frame(frame)
        right_frame.grid(row=1, column=1, sticky=tk.NSEW)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        # Results frame on the left
        results_frame = ttk.LabelFrame(left_frame, text="Calculation Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results table
        self.thermo_results_tree = ttk.Treeview(results_frame, columns=("parameter", "value", "unit"), show="headings", height=12)
        self.thermo_results_tree.heading("parameter", text="Parameter")
        self.thermo_results_tree.heading("value", text="Value")
        self.thermo_results_tree.heading("unit", text="Unit")
        
        self.thermo_results_tree.column("parameter", width=200)
        self.thermo_results_tree.column("value", width=100)
        self.thermo_results_tree.column("unit", width=100)
        
        # Add some default rows
        self.thermo_results_tree.insert("", tk.END, values=("Temperature Difference", "--", "K"))
        self.thermo_results_tree.insert("", tk.END, values=("Density Change", "--", "kg/m³"))
        self.thermo_results_tree.insert("", tk.END, values=("Driving Pressure", "--", "Pa"))
        self.thermo_results_tree.insert("", tk.END, values=("Flow Rate", "--", "kg/s"))
        self.thermo_results_tree.insert("", tk.END, values=("Volumetric Flow", "--", "L/s"))
        self.thermo_results_tree.insert("", tk.END, values=("Flow Velocity", "--", "m/s"))
        self.thermo_results_tree.insert("", tk.END, values=("Heat Capacity", "--", "kW"))
        self.thermo_results_tree.insert("", tk.END, values=("System Efficiency", "--", "%"))
        
        self.thermo_results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visualization frame on the right
        viz_frame = ttk.LabelFrame(right_frame, text="Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Placeholder for visualization
        self.thermo_canvas_frame = ttk.Frame(viz_frame)
        self.thermo_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a simple diagram of a thermosiphon system
        self.create_thermosiphon_diagram(self.thermo_canvas_frame)
    
    def setup_heat_pipe_tab(self):
        """Set up the heat pipe tab."""
        frame = ttk.Frame(self.heat_pipe_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Heat Pipe System Analysis", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        # Split into two columns
        left_frame = ttk.Frame(frame)
        left_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        
        right_frame = ttk.Frame(frame)
        right_frame.grid(row=1, column=1, sticky=tk.NSEW)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        # Results frame on the left
        results_frame = ttk.LabelFrame(left_frame, text="Calculation Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results table
        self.heat_pipe_results_tree = ttk.Treeview(results_frame, columns=("parameter", "value", "unit"), show="headings", height=10)
        self.heat_pipe_results_tree.heading("parameter", text="Parameter")
        self.heat_pipe_results_tree.heading("value", text="Value")
        self.heat_pipe_results_tree.heading("unit", text="Unit")
        
        self.heat_pipe_results_tree.column("parameter", width=200)
        self.heat_pipe_results_tree.column("value", width=100)
        self.heat_pipe_results_tree.column("unit", width=100)
        
        # Add some default rows
        self.heat_pipe_results_tree.insert("", tk.END, values=("Heat Pipe Capacity", "--", "W"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Total Capacity", "--", "kW"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Stage 1 Capacity", "--", "kW"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Stage 2 Capacity", "--", "kW"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Effective Conductivity", "--", "W/m·K"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Copper Ratio", "--", "x"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("System Efficiency", "--", "%"))
        
        self.heat_pipe_results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visualization frame on the right
        viz_frame = ttk.LabelFrame(right_frame, text="Heat Pipe Design")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Placeholder for visualization
        self.heat_pipe_canvas_frame = ttk.Frame(viz_frame)
        self.heat_pipe_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a simple diagram of a heat pipe system
        self.create_heat_pipe_diagram(self.heat_pipe_canvas_frame)
    
    def setup_pcm_tab(self):
        """Set up the PCM tab."""
        frame = ttk.Frame(self.pcm_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Phase Change Material Analysis", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        # Split into two columns
        left_frame = ttk.Frame(frame)
        left_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        
        right_frame = ttk.Frame(frame)
        right_frame.grid(row=1, column=1, sticky=tk.NSEW)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        # Results frame on the left
        results_frame = ttk.LabelFrame(left_frame, text="Calculation Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results table
        self.pcm_results_tree = ttk.Treeview(results_frame, columns=("parameter", "value", "unit"), show="headings", height=10)
        self.pcm_results_tree.heading("parameter", text="Parameter")
        self.pcm_results_tree.heading("value", text="Value")
        self.pcm_results_tree.heading("unit", text="Unit")
        
        self.pcm_results_tree.column("parameter", width=200)
        self.pcm_results_tree.column("value", width=100)
        self.pcm_results_tree.column("unit", width=100)
        
        # Add some default rows
        self.pcm_results_tree.insert("", tk.END, values=("PCM Mass", "--", "kg"))
        self.pcm_results_tree.insert("", tk.END, values=("Sensible Heat (Solid)", "--", "kJ"))
        self.pcm_results_tree.insert("", tk.END, values=("Latent Heat Capacity", "--", "kJ"))
        self.pcm_results_tree.insert("", tk.END, values=("Sensible Heat (Liquid)", "--", "kJ"))
        self.pcm_results_tree.insert("", tk.END, values=("Total Energy Storage", "--", "kJ"))
        self.pcm_results_tree.insert("", tk.END, values=("Storage Time", "--", "min"))
        self.pcm_results_tree.insert("", tk.END, values=("Energy Density", "--", "kWh/m³"))
        
        self.pcm_results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visualization frame on the right
        viz_frame = ttk.LabelFrame(right_frame, text="Phase Change Process")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Placeholder for visualization
        self.pcm_canvas_frame = ttk.Frame(viz_frame)
        self.pcm_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a simple diagram of PCM operation
        self.create_pcm_diagram(self.pcm_canvas_frame)
    
    def setup_dimple_tab(self):
        """Set up the dimpled surface tab."""
        frame = ttk.Frame(self.dimple_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Dimpled Surface Analysis", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        # Split into two columns
        left_frame = ttk.Frame(frame)
        left_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        
        right_frame = ttk.Frame(frame)
        right_frame.grid(row=1, column=1, sticky=tk.NSEW)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        # Results frame on the left
        results_frame = ttk.LabelFrame(left_frame, text="Calculation Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results table
        self.dimple_results_tree = ttk.Treeview(results_frame, columns=("parameter", "value", "unit"), show="headings", height=10)
        self.dimple_results_tree.heading("parameter", text="Parameter")
        self.dimple_results_tree.heading("value", text="Value")
        self.dimple_results_tree.heading("unit", text="Unit")
        
        self.dimple_results_tree.column("parameter", width=200)
        self.dimple_results_tree.column("value", width=100)
        self.dimple_results_tree.column("unit", width=100)
        
        # Add some default rows
        self.dimple_results_tree.insert("", tk.END, values=("Total Dimples", "--", ""))
        self.dimple_results_tree.insert("", tk.END, values=("Enhanced Surface Area", "--", "m²"))
        self.dimple_results_tree.insert("", tk.END, values=("Enhanced Heat Transfer Coefficient", "--", "W/m²·K"))
        self.dimple_results_tree.insert("", tk.END, values=("Temperature Difference", "--", "K"))
        self.dimple_results_tree.insert("", tk.END, values=("Base Heat Dissipation", "--", "kW"))
        self.dimple_results_tree.insert("", tk.END, values=("Enhanced Heat Dissipation", "--", "kW"))
        self.dimple_results_tree.insert("", tk.END, values=("Improvement", "--", "%"))
        
        self.dimple_results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visualization frame on the right
        viz_frame = ttk.LabelFrame(right_frame, text="Dimpled Surface Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Placeholder for visualization
        self.dimple_canvas_frame = ttk.Frame(viz_frame)
        self.dimple_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a simple diagram of dimpled surfaces
        self.create_dimple_diagram(self.dimple_canvas_frame)
    
    def setup_rdh_tab(self):
        """Set up the rear door heat exchanger tab."""
        frame = ttk.Frame(self.rdh_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Rear Door Heat Exchanger Analysis", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        # Split into left input and right results
        left_frame = ttk.Frame(frame)
        left_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        
        right_frame = ttk.Frame(frame)
        right_frame.grid(row=1, column=1, sticky=tk.NSEW)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        # Input parameters frame
        input_frame = ttk.LabelFrame(left_frame, text="RDHx Parameters")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create input fields
        row = 0
        
        # Server Heat Load
        ttk.Label(input_frame, text="Server Heat Load (kW):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_heat_load_var = tk.DoubleVar(value=self.rdh_params["server_heat_load"])
        rdh_heat_load_entry = ttk.Entry(input_frame, textvariable=self.rdh_heat_load_var, width=10)
        rdh_heat_load_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Inlet Water Temperature
        ttk.Label(input_frame, text="Inlet Water Temperature (°C):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_inlet_water_var = tk.DoubleVar(value=self.rdh_params["inlet_water_temp"])
        rdh_inlet_water_entry = ttk.Entry(input_frame, textvariable=self.rdh_inlet_water_var, width=10)
        rdh_inlet_water_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Outlet Water Temperature
        ttk.Label(input_frame, text="Outlet Water Temperature (°C):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_outlet_water_var = tk.DoubleVar(value=self.rdh_params["outlet_water_temp"])
        rdh_outlet_water_entry = ttk.Entry(input_frame, textvariable=self.rdh_outlet_water_var, width=10)
        rdh_outlet_water_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Inlet Air Temperature
        ttk.Label(input_frame, text="Inlet Air Temperature (°C):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_inlet_air_var = tk.DoubleVar(value=self.rdh_params["inlet_air_temp"])
        rdh_inlet_air_entry = ttk.Entry(input_frame, textvariable=self.rdh_inlet_air_var, width=10)
        rdh_inlet_air_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Outlet Air Temperature
        ttk.Label(input_frame, text="Outlet Air Temperature (°C):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_outlet_air_var = tk.DoubleVar(value=self.rdh_params["outlet_air_temp"])
        rdh_outlet_air_entry = ttk.Entry(input_frame, textvariable=self.rdh_outlet_air_var, width=10)
        rdh_outlet_air_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Water Flow Rate
        ttk.Label(input_frame, text="Water Flow Rate (L/s):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_water_flow_var = tk.DoubleVar(value=self.rdh_params["water_flow_rate"])
        rdh_water_flow_entry = ttk.Entry(input_frame, textvariable=self.rdh_water_flow_var, width=10)
        rdh_water_flow_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Air Flow Rate
        ttk.Label(input_frame, text="Air Flow Rate (m³/h):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_air_flow_var = tk.DoubleVar(value=self.rdh_params["air_flow_rate"])
        rdh_air_flow_entry = ttk.Entry(input_frame, textvariable=self.rdh_air_flow_var, width=10)
        rdh_air_flow_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Fan Count
        ttk.Label(input_frame, text="Fan Count:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_fan_count_var = tk.IntVar(value=self.rdh_params["fan_count"])
        rdh_fan_count_entry = ttk.Entry(input_frame, textvariable=self.rdh_fan_count_var, width=10)
        rdh_fan_count_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Coil Rows
        ttk.Label(input_frame, text="Coil Rows:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_coil_rows_var = tk.IntVar(value=self.rdh_params["coil_rows"])
        rdh_coil_rows_entry = ttk.Entry(input_frame, textvariable=self.rdh_coil_rows_var, width=10)
        rdh_coil_rows_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Door Dimensions
        ttk.Label(input_frame, text="Door Width (m):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_door_width_var = tk.DoubleVar(value=self.rdh_params["door_width"])
        rdh_door_width_entry = ttk.Entry(input_frame, textvariable=self.rdh_door_width_var, width=10)
        rdh_door_width_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        ttk.Label(input_frame, text="Door Height (m):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rdh_door_height_var = tk.DoubleVar(value=self.rdh_params["door_height"])
        rdh_door_height_entry = ttk.Entry(input_frame, textvariable=self.rdh_door_height_var, width=10)
        rdh_door_height_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        
        # Calculate button
        calculate_button = ttk.Button(input_frame, text="Calculate RDHx", command=self.calculate_rdh, style='Primary.TButton')
        calculate_button.grid(row=row, column=0, columnspan=2, pady=10)
        
        # Results frame on the right
        results_frame = ttk.LabelFrame(right_frame, text="RDHx Performance")
        results_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        
        # Results table
        self.rdh_results_tree = ttk.Treeview(results_frame, columns=("parameter", "value", "unit"), show="headings", height=10)
        self.rdh_results_tree.heading("parameter", text="Parameter")
        self.rdh_results_tree.heading("value", text="Value")
        self.rdh_results_tree.heading("unit", text="Unit")
        
        self.rdh_results_tree.column("parameter", width=240)
        self.rdh_results_tree.column("value", width=100)
        self.rdh_results_tree.column("unit", width=100)
        
        # Add some default rows
        self.rdh_results_tree.insert("", tk.END, values=("Water Heat Capacity", "--", "kW"))
        self.rdh_results_tree.insert("", tk.END, values=("Air Heat Capacity", "--", "kW"))
        self.rdh_results_tree.insert("", tk.END, values=("Effectiveness", "--", "%"))
        self.rdh_results_tree.insert("", tk.END, values=("Heat Transfer Coefficient", "--", "W/m²·K"))
        self.rdh_results_tree.insert("", tk.END, values=("Passive Cooling Capacity", "--", "kW"))
        self.rdh_results_tree.insert("", tk.END, values=("Passive Percentage", "--", "%"))
        self.rdh_results_tree.insert("", tk.END, values=("Thermal Coverage", "--", "%"))
        self.rdh_results_tree.insert("", tk.END, values=("Water Velocity", "--", "m/s"))
        self.rdh_results_tree.insert("", tk.END, values=("Air Velocity", "--", "m/s"))
        self.rdh_results_tree.insert("", tk.END, values=("Fan Power", "--", "kW"))
        
        self.rdh_results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # RDHx visualization
        viz_frame = ttk.LabelFrame(right_frame, text="RDHx Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.rdh_canvas_frame = ttk.Frame(viz_frame)
        self.rdh_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create RDHx diagram
        self.create_rdh_diagram(self.rdh_canvas_frame)
    
    def setup_results_tab(self):
        """Set up the results tab with overall system performance."""
        frame = ttk.Frame(self.results_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="System Performance Summary", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        # Split into two columns
        left_frame = ttk.Frame(frame)
        left_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        
        right_frame = ttk.Frame(frame)
        right_frame.grid(row=1, column=1, sticky=tk.NSEW)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        # Results frame on the left
        results_frame = ttk.LabelFrame(left_frame, text="System Performance Metrics")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results table
        self.system_results_tree = ttk.Treeview(results_frame, columns=("parameter", "value", "unit"), show="headings", height=12)
        self.system_results_tree.heading("parameter", text="Parameter")
        self.system_results_tree.heading("value", text="Value")
        self.system_results_tree.heading("unit", text="Unit")
        
        self.system_results_tree.column("parameter", width=200)
        self.system_results_tree.column("value", width=100)
        self.system_results_tree.column("unit", width=100)
        
        # Add some default rows
        self.system_results_tree.insert("", tk.END, values=("Heat Load", "--", "kW"))
        self.system_results_tree.insert("", tk.END, values=("Thermosiphon Capacity", "--", "kW"))
        self.system_results_tree.insert("", tk.END, values=("Heat Pipe Capacity", "--", "kW"))
        self.system_results_tree.insert("", tk.END, values=("PCM Buffer Capacity", "--", "kWh"))
        self.system_results_tree.insert("", tk.END, values=("AHU Dissipation", "--", "kW"))
        self.system_results_tree.insert("", tk.END, values=("Thermal Load Coverage", "--", "%"))
        self.system_results_tree.insert("", tk.END, values=("Buffer Time", "--", "min"))
        self.system_results_tree.insert("", tk.END, values=("Conventional PUE", "--", ""))
        self.system_results_tree.insert("", tk.END, values=("Passive System PUE", "--", ""))
        self.system_results_tree.insert("", tk.END, values=("Energy Savings", "--", "MWh/year"))
        self.system_results_tree.insert("", tk.END, values=("Cost Savings", "--", "$/year"))
        self.system_results_tree.insert("", tk.END, values=("CO₂ Reduction", "--", "tonnes/year"))
        self.system_results_tree.insert("", tk.END, values=("ROI Period", "--", "years"))
        
        self.system_results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visualization frame on the right
        viz_frame = ttk.LabelFrame(right_frame, text="Performance Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Canvas for matplotlib charts
        self.chart_canvas_frame = ttk.Frame(viz_frame)
        self.chart_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add report generation button
        report_button = ttk.Button(frame, text="Generate Full Report", command=self.generate_reports, style='Success.TButton')
        report_button.grid(row=2, column=0, columnspan=2, pady=10)
    
    def create_thermosiphon_diagram(self, parent):
        """Create a simple diagram of a thermosiphon system."""
        canvas = tk.Canvas(parent, bg="white", width=400, height=400)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw AHU at the top
        canvas.create_rectangle(100, 50, 300, 100, fill="#cfe2ff", outline="#0d6efd", width=2)
        canvas.create_text(200, 75, text="Cold Reservoir (AHU)", font=("Arial", 10, "bold"))
        
        # Draw server rack at the bottom
        canvas.create_rectangle(100, 300, 300, 350, fill="#6c757d", outline="#343a40", width=2)
        canvas.create_text(200, 325, text="Server Rack", font=("Arial", 10, "bold"))
        
        # Draw thermosiphon pipes
        # Cold down pipe
        canvas.create_rectangle(150, 100, 170, 300, fill="#90e0ef", outline="#0d6efd", width=2)
        # Hot up pipe
        canvas.create_rectangle(230, 100, 250, 300, fill="#ff6b6b", outline="#dc3545", width=2)
        
        # Add arrows for flow direction
        # Cold down arrows
        for y in range(130, 271, 40):
            canvas.create_polygon(160, y, 155, y+10, 165, y+10, fill="#0d6efd", outline="#0d6efd")
        
        # Hot up arrows
        for y in range(270, 129, -40):
            canvas.create_polygon(240, y, 235, y-10, 245, y-10, fill="#dc3545", outline="#dc3545")
        
        # Add temperature labels
        canvas.create_text(120, 75, text="30-40°C", font=("Arial", 8))
        canvas.create_text(280, 325, text="50-60°C", font=("Arial", 8))
        
        # Add height indicator
        canvas.create_line(350, 100, 350, 300, width=2, arrow="both")
        canvas.create_text(370, 200, text="Height\nDifferential", font=("Arial", 8))
        
        # Add legend
        canvas.create_rectangle(50, 370, 70, 380, fill="#90e0ef", outline="#0d6efd")
        canvas.create_text(110, 375, text="Cold Water Flow", font=("Arial", 8), anchor=tk.W)
        
        canvas.create_rectangle(200, 370, 220, 380, fill="#ff6b6b", outline="#dc3545")
        canvas.create_text(260, 375, text="Hot Water Flow", font=("Arial", 8), anchor=tk.W)
    
    def create_heat_pipe_diagram(self, parent):
        """Create a simple diagram of heat pipe operation."""
        canvas = tk.Canvas(parent, bg="white", width=400, height=400)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw heat pipe
        canvas.create_rectangle(50, 180, 350, 220, fill="#f8f9fa", outline="#6c757d", width=2)
        
        # Draw evaporator section
        canvas.create_rectangle(50, 180, 150, 220, fill="#ff8c8c", outline="#dc3545", width=2)
        canvas.create_text(100, 200, text="Evaporator", font=("Arial", 10, "bold"))
        
        # Draw condenser section
        canvas.create_rectangle(250, 180, 350, 220, fill="#90e0ef", outline="#0d6efd", width=2)
        canvas.create_text(300, 200, text="Condenser", font=("Arial", 10, "bold"))
        
        # Draw vapor flow
        canvas.create_rectangle(150, 185, 250, 200, fill="#ffe0e0", outline="#dc3545", width=1, dash=(4, 2))
        canvas.create_text(200, 192, text="Vapor Flow", font=("Arial", 8))
        
        # Draw liquid return
        canvas.create_rectangle(150, 200, 250, 215, fill="#e7f5ff", outline="#0d6efd", width=1, dash=(4, 2))
        canvas.create_text(200, 208, text="Liquid Return", font=("Arial", 8))
        
        # Draw flow arrows
        canvas.create_polygon(240, 192, 230, 187, 230, 197, fill="#dc3545", outline="#dc3545")
        canvas.create_polygon(160, 208, 170, 203, 170, 213, fill="#0d6efd", outline="#0d6efd")
        
        # Draw heat source and heat sink
        canvas.create_rectangle(75, 230, 125, 250, fill="#dc3545", outline="#b02a37", width=2)
        canvas.create_text(100, 240, text="Heat Source", font=("Arial", 8))
        
        canvas.create_rectangle(275, 150, 325, 170, fill="#0d6efd", outline="#0a58ca", width=2)
        canvas.create_text(300, 160, text="Heat Sink", font=("Arial", 8))
        
        # Draw heat arrows
        for x in range(85, 121, 10):
            canvas.create_polygon(x, 230, x-5, 220, x+5, 220, fill="#dc3545", outline="#dc3545")
        
        for x in range(285, 321, 10):
            canvas.create_polygon(x, 170, x-5, 180, x+5, 180, fill="#0d6efd", outline="#0d6efd")
        
        # Draw two-stage system below
        canvas.create_text(200, 280, text="Two-Stage Heat Pipe System", font=("Arial", 12, "bold"))
        
        # First stage
        canvas.create_rectangle(75, 310, 175, 340, fill="#ff8c8c", outline="#dc3545", width=2)
        canvas.create_text(125, 325, text="Stage 1: 50-60°C", font=("Arial", 8))
        
        # Interface
        canvas.create_rectangle(175, 310, 225, 340, fill="#f8f9fa", outline="#6c757d", width=2)
        canvas.create_text(200, 325, text="Interface", font=("Arial", 8))
        
        # Second stage
        canvas.create_rectangle(225, 310, 325, 340, fill="#ffc107", outline="#fd7e14", width=2)
        canvas.create_text(275, 325, text="Stage 2: 40-50°C", font=("Arial", 8))
        
        # Add arrows
        canvas.create_polygon(210, 325, 200, 320, 200, 330, fill="#6c757d", outline="#6c757d")
    
    def create_pcm_diagram(self, parent):
        """Create a simple diagram of PCM operation."""
        canvas = tk.Canvas(parent, bg="white", width=400, height=400)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw PCM module
        canvas.create_rectangle(100, 150, 300, 250, fill="#ade8f4", outline="#0096c7", width=2)
        canvas.create_text(200, 170, text="Phase Change Material", font=("Arial", 12, "bold"))
        canvas.create_text(200, 190, text="CaCl₂·6H₂O", font=("Arial", 10))
        canvas.create_text(200, 210, text="Melting Point: 29°C", font=("Arial", 10))
        canvas.create_text(200, 230, text="Latent Heat: 190 kJ/kg", font=("Arial", 10))
        
        # Draw phase change process below
        y_pos = 280
        
        # Draw arrow
        canvas.create_line(50, y_pos+40, 350, y_pos+40, arrow=tk.LAST, width=2)
        canvas.create_text(200, y_pos+60, text="Temperature Increase", font=("Arial", 8))
        
        # Draw phase states
        # Solid
        canvas.create_rectangle(50, y_pos, 100, y_pos+30, fill="#caf0f8", outline="#0096c7", width=1)
        canvas.create_text(75, y_pos+15, text="Solid", font=("Arial", 8))
        
        # Starting to melt
        canvas.create_rectangle(100, y_pos, 150, y_pos+30, fill="#90e0ef", outline="#0096c7", width=1)
        canvas.create_text(125, y_pos+15, text="Melting\nBegins", font=("Arial", 8))
        
        # Melting (phase change)
        canvas.create_rectangle(150, y_pos, 250, y_pos+30, fill="#48cae4", outline="#0096c7", width=1)
        canvas.create_text(200, y_pos+15, text="Phase Change\nat 29°C", font=("Arial", 8))
        
        # Almost liquid
        canvas.create_rectangle(250, y_pos, 300, y_pos+30, fill="#00b4d8", outline="#0096c7", width=1)
        canvas.create_text(275, y_pos+15, text="Melting\nComplete", font=("Arial", 8))
        
        # Liquid
        canvas.create_rectangle(300, y_pos, 350, y_pos+30, fill="#0096c7", outline="#0096c7", width=1)
        canvas.create_text(325, y_pos+15, text="Liquid", font=("Arial", 8))
        
        # Draw energy absorption graph
        # Axes
        canvas.create_line(50, 380, 350, 380, width=2)  # x-axis
        canvas.create_line(50, 380, 50, 280, width=2)  # y-axis
        
        # Labels
        canvas.create_text(35, 330, text="Energy\nAbsorbed", font=("Arial", 8))
        canvas.create_text(200, 395, text="Temperature", font=("Arial", 8))
        
        # Energy curve
        canvas.create_line(
            50, 360,  # Start
            150, 350,  # Approach phase change
            150, 320,  # Start of phase change (vertical line)
            250, 320,  # During phase change (horizontal line - latent heat)
            250, 290,  # End of phase change (vertical line)
            350, 280,  # Final temp
            smooth=1, width=2, fill="#0096c7"
        )
        
        # Phase change region
        canvas.create_rectangle(150, 320, 250, 380, fill="#48cae4", stipple="gray50", outline="")
    
    def create_dimple_diagram(self, parent):
        """Create a simple diagram comparing flat and dimpled surfaces."""
        canvas = tk.Canvas(parent, bg="white", width=400, height=400)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Title
        canvas.create_text(200, 30, text="Flat vs. Dimpled Surface Comparison", font=("Arial", 12, "bold"))
        
        # Draw flat surface on left
        canvas.create_text(100, 60, text="Flat Surface", font=("Arial", 10, "bold"))
        canvas.create_rectangle(50, 80, 150, 220, fill="#e9ecef", outline="#adb5bd", width=2)
        canvas.create_line(50, 80, 150, 80, width=3, fill="#adb5bd")
        
        # Draw airflow over flat surface
        for y in range(100, 221, 30):
            canvas.create_line(30, y, 170, y, smooth=1, dash=(4, 2), fill="#6c757d")
        
        # Draw boundary layer
        canvas.create_line(50, 80, 50, 220, dash=(3, 3), fill="#adb5bd")
        canvas.create_line(55, 80, 55, 220, width=2, fill="#dc3545")
        canvas.create_text(65, 150, text="Boundary\nLayer", font=("Arial", 8), anchor=tk.W)
        
        # Draw dimpled surface on right
        canvas.create_text(300, 60, text="Dimpled Surface", font=("Arial", 10, "bold"))
        canvas.create_rectangle(250, 80, 350, 220, fill="#e9ecef", outline="#adb5bd", width=2)
        
        # Draw dimples
        for y in range(80, 221, 35):
            # Draw a dimple
            canvas.create_arc(280, y, 320, y+20, start=0, extent=180, style=tk.ARC, outline="#adb5bd", width=2)
            canvas.create_line(280, y+10, 250, y+10, fill="#adb5bd", width=2)
            canvas.create_line(320, y+10, 350, y+10, fill="#adb5bd", width=2)
        
        # Draw turbulent airflow over dimpled surface
        canvas.create_line(230, 100, 370, 100, smooth=1, splinesteps=20, dash=(4, 2), fill="#6c757d")
        canvas.create_line(230, 130, 370, 130, smooth=1, splinesteps=20, dash=(4, 2), fill="#6c757d")
        canvas.create_line(230, 160, 370, 160, smooth=1, splinesteps=20, dash=(4, 2), fill="#6c757d")
        canvas.create_line(230, 190, 370, 190, smooth=1, splinesteps=20, dash=(4, 2), fill="#6c757d")
        
        # Draw vortices in dimples
        for y in range(95, 211, 35):
            canvas.create_oval(290, y, 310, y+10, outline="#dc3545", width=1)
            canvas.create_arc(295, y, 305, y+10, start=0, extent=270, style=tk.ARC, outline="#dc3545", width=1)
        
        # Performance comparison
        canvas.create_rectangle(50, 250, 350, 380, fill="#f8f9fa", outline="#6c757d", width=2)
        canvas.create_text(200, 270, text="Performance Comparison", font=("Arial", 10, "bold"))
        
        # Metrics table
        canvas.create_line(50, 290, 350, 290, fill="#6c757d")
        canvas.create_line(200, 290, 200, 380, fill="#6c757d")
        
        # Headers
        canvas.create_text(125, 300, text="Flat Surface", font=("Arial", 9, "bold"))
        canvas.create_text(275, 300, text="Dimpled Surface", font=("Arial", 9, "bold"))
        
        # Metrics
        y_pos = 320
        metrics = [
            "Heat Transfer Coefficient",
            "Boundary Layer",
            "Surface Area",
            "Vortex Formation"
        ]
        
        flat_values = [
            "15 W/m²·K",
            "Thick",
            "1x",
            "None"
        ]
        
        dimpled_values = [
            "33 W/m²·K (+120%)",
            "Disrupted",
            "1.7x",
            "Strong"
        ]
        
        for i, metric in enumerate(metrics):
            canvas.create_text(60, y_pos + i*20, text=metric, font=("Arial", 8), anchor=tk.W)
            canvas.create_text(125, y_pos + i*20, text=flat_values[i], font=("Arial", 8))
            canvas.create_text(275, y_pos + i*20, text=dimpled_values[i], font=("Arial", 8))
    
    def create_rdh_diagram(self, parent):
        """Create a diagram of the rear door heat exchanger."""
        canvas = tk.Canvas(parent, bg="white", width=400, height=400)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw server rack
        canvas.create_rectangle(50, 100, 150, 300, fill="#6c757d", outline="#343a40", width=2)
        canvas.create_text(100, 320, text="Server Rack", font=("Arial", 10))
        
        # Draw server units in rack
        for y in range(120, 281, 30):
            canvas.create_rectangle(60, y, 140, y+20, fill="#495057", outline="#343a40", width=1)
        
        # Draw RDHx door
        canvas.create_rectangle(150, 100, 180, 300, fill="#f8f9fa", outline="#343a40", width=2)
        canvas.create_text(165, 320, text="RDHx", font=("Arial", 10))
        
        # Draw coils in door
        for y in range(110, 291, 20):
            canvas.create_line(153, y, 177, y, fill="#0d6efd", width=2)
        
        # Draw manifolds
        canvas.create_rectangle(150, 80, 180, 100, fill="#0d6efd", outline="#0a58ca", width=2)
        canvas.create_text(165, 90, text="In", font=("Arial", 8), fill="white")
        
        canvas.create_rectangle(150, 300, 180, 320, fill="#dc3545", outline="#b02a37", width=2)
        canvas.create_text(165, 310, text="Out", font=("Arial", 8), fill="white")
        
        # Draw airflow
        # Hot air from servers
        for x in range(170, 221, 10):
            canvas.create_line(150, x, 180, x, arrow=tk.LAST, fill="#dc3545", width=1)
        
        # Cooled air out
        for x in range(170, 221, 10):
            canvas.create_line(180, x, 210, x, arrow=tk.LAST, fill="#0d6efd", width=1)
        
        # Add temperature labels
        canvas.create_text(135, 200, text="Hot Air\n(50°C)", font=("Arial", 8), fill="#dc3545")
        canvas.create_text(225, 200, text="Cool Air\n(22°C)", font=("Arial", 8), fill="#0d6efd")
        
        # Add water flow indicators
        canvas.create_text(165, 70, text="Cold Water In\n(18°C)", font=("Arial", 8), fill="#0d6efd")
        canvas.create_text(165, 340, text="Warm Water Out\n(28°C)", font=("Arial", 8), fill="#dc3545")
        
        # Draw a section view of door
        canvas.create_text(300, 80, text="Door Cross-Section", font=("Arial", 10, "bold"))
        
        # Door outline
        canvas.create_rectangle(250, 100, 350, 300, fill="#f8f9fa", outline="#343a40", width=2)
        
        # Coil rows
        y_pos = 120
        for i in range(6):  # 6 coil rows
            for x in range(260, 341, 20):
                canvas.create_oval(x-5, y_pos-5, x+5, y_pos+5, fill="#0d6efd", outline="#0a58ca")
            y_pos += 30
        
        # Air flow arrows
        canvas.create_polygon(230, 200, 250, 190, 250, 210, fill="#dc3545", outline="#dc3545")
        canvas.create_polygon(370, 200, 350, 190, 350, 210, fill="#0d6efd", outline="#0d6efd")
        
        # Add labels
        canvas.create_text(230, 180, text="Hot Air In", font=("Arial", 8), anchor=tk.E)
        canvas.create_text(370, 180, text="Cool Air Out", font=("Arial", 8), anchor=tk.W)
        
        # Add performance graph at bottom
        canvas.create_text(300, 330, text="Cooling Capacity vs. Airflow", font=("Arial", 10, "bold"))
        
        # Graph axes
        canvas.create_line(250, 380, 350, 380, arrow=tk.LAST, width=1)  # x-axis
        canvas.create_line(250, 380, 250, 350, arrow=tk.LAST, width=1)  # y-axis
        
        # Graph line
        canvas.create_line(250, 375, 270, 370, 290, 365, 310, 357, 330, 353, 350, 352, smooth=1, fill="#dc3545", width=2)
        
        # Labels
        canvas.create_text(300, 390, text="Airflow Rate", font=("Arial", 8))
        canvas.create_text(240, 365, text="Capacity", font=("Arial", 8), angle=90)
    
    def update_main_summary(self, results):
        """Update the summary section on the main tab."""
        system_perf = results["system_performance"]
        
        # Update summary labels
        self.coverage_label.config(text=f"Thermal Coverage: {system_perf['thermal_coverage']:.1f}%")
        self.buffer_label.config(text=f"Buffer Time: {system_perf['buffer_time']:.1f} min")
        self.roi_label.config(text=f"ROI Period: {system_perf['roi_period']:.2f} years")
        self.efficiency_label.config(text=f"System Efficiency: {min(system_perf['thermal_coverage'], 100):.1f}%")
    
    def update_thermosiphon_results(self, results):
        """Update the thermosiphon results tree."""
        thermo = results["thermosiphon"]
        
        # Clear existing data
        for item in self.thermo_results_tree.get_children():
            self.thermo_results_tree.delete(item)
        
        # Add new data
        self.thermo_results_tree.insert("", tk.END, values=("Temperature Difference", f"{thermo['temp_diff']:.2f}", "K"))
        self.thermo_results_tree.insert("", tk.END, values=("Density Change", f"{thermo['density_change']:.4f}", "kg/m³"))
        self.thermo_results_tree.insert("", tk.END, values=("Driving Pressure", f"{thermo['driving_pressure']:.2f}", "Pa"))
        self.thermo_results_tree.insert("", tk.END, values=("Flow Rate", f"{thermo['flow_rate']:.2f}", "kg/s"))
        self.thermo_results_tree.insert("", tk.END, values=("Volumetric Flow", f"{thermo['volumetric_flow']:.2f}", "L/s"))
        self.thermo_results_tree.insert("", tk.END, values=("Flow Velocity", f"{thermo['flow_velocity']:.2f}", "m/s"))
        self.thermo_results_tree.insert("", tk.END, values=("Heat Capacity", f"{thermo['heat_capacity']:.2f}", "kW"))
        self.thermo_results_tree.insert("", tk.END, values=("System Efficiency", f"{thermo['system_efficiency']:.2f}", "%"))
    
    def update_heat_pipe_results(self, results):
        """Update the heat pipe results tree."""
        heat_pipes = results["heat_pipes"]
        
        # Clear existing data
        for item in self.heat_pipe_results_tree.get_children():
            self.heat_pipe_results_tree.delete(item)
        
        # Add new data
        self.heat_pipe_results_tree.insert("", tk.END, values=("Heat Pipe Capacity", f"{heat_pipes['heat_pipe_capacity']:.2f}", "W"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Total Capacity", f"{heat_pipes['total_capacity']:.2f}", "kW"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Stage 1 Capacity", f"{heat_pipes['stage1_capacity']:.2f}", "kW"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Stage 2 Capacity", f"{heat_pipes['stage2_capacity']:.2f}", "kW"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Effective Conductivity", f"{heat_pipes['effective_conductivity']:.0f}", "W/m·K"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("Copper Ratio", f"{heat_pipes['copper_ratio']:.0f}", "x"))
        self.heat_pipe_results_tree.insert("", tk.END, values=("System Efficiency", f"{heat_pipes['system_efficiency']:.2f}", "%"))
    
    def update_pcm_results(self, results):
        """Update the PCM results tree."""
        pcm = results["pcm"]
        
        # Clear existing data
        for item in self.pcm_results_tree.get_children():
            self.pcm_results_tree.delete(item)
        
        # Add new data
        self.pcm_results_tree.insert("", tk.END, values=("PCM Mass", f"{pcm['pcm_mass']:.2f}", "kg"))
        self.pcm_results_tree.insert("", tk.END, values=("Sensible Heat (Solid)", f"{pcm['sensible_heat_solid']:.2f}", "kJ"))
        self.pcm_results_tree.insert("", tk.END, values=("Latent Heat Capacity", f"{pcm['latent_heat_capacity']:.2f}", "kJ"))
        self.pcm_results_tree.insert("", tk.END, values=("Sensible Heat (Liquid)", f"{pcm['sensible_heat_liquid']:.2f}", "kJ"))
        self.pcm_results_tree.insert("", tk.END, values=("Total Energy Storage", f"{pcm['total_energy']:.2f}", "kJ"))
        self.pcm_results_tree.insert("", tk.END, values=("Storage Time", f"{pcm['storage_time']:.2f}", "min"))
        self.pcm_results_tree.insert("", tk.END, values=("Energy Density", f"{pcm['energy_density']:.2f}", "kWh/m³"))
    
    def update_dimple_results(self, results):
        """Update the dimpled surface results tree."""
        dimple = results["dimpled_surface"]
        
        # Clear existing data
        for item in self.dimple_results_tree.get_children():
            self.dimple_results_tree.delete(item)
        
        # Add new data
        self.dimple_results_tree.insert("", tk.END, values=("Total Dimples", f"{dimple['total_dimples']:.0f}", ""))
        self.dimple_results_tree.insert("", tk.END, values=("Enhanced Surface Area", f"{dimple['enhanced_area']:.2f}", "m²"))
        self.dimple_results_tree.insert("", tk.END, values=("Enhanced Heat Transfer Coefficient", f"{dimple['enhanced_coefficient']:.2f}", "W/m²·K"))
        self.dimple_results_tree.insert("", tk.END, values=("Temperature Difference", f"{dimple['temp_diff']:.2f}", "K"))
        self.dimple_results_tree.insert("", tk.END, values=("Base Heat Dissipation", f"{dimple['base_dissipation']:.2f}", "kW"))
        self.dimple_results_tree.insert("", tk.END, values=("Enhanced Heat Dissipation", f"{dimple['enhanced_dissipation']:.2f}", "kW"))
        self.dimple_results_tree.insert("", tk.END, values=("Improvement", f"{dimple['improvement']:.2f}", "%"))
    
    def update_rdh_results(self, results):
        """Update the RDHx results tree."""
        # Clear existing data
        for item in self.rdh_results_tree.get_children():
            self.rdh_results_tree.delete(item)
        
        # Add new data
        self.rdh_results_tree.insert("", tk.END, values=("Water Heat Capacity", f"{results['water_heat_capacity']:.2f}", "kW"))
        self.rdh_results_tree.insert("", tk.END, values=("Air Heat Capacity", f"{results['air_heat_capacity']:.2f}", "kW"))
        self.rdh_results_tree.insert("", tk.END, values=("Effectiveness", f"{results['effectiveness']:.2f}", "%"))
        self.rdh_results_tree.insert("", tk.END, values=("Heat Transfer Coefficient", f"{results['heat_transfer_coefficient']:.2f}", "W/m²·K"))
        self.rdh_results_tree.insert("", tk.END, values=("Passive Cooling Capacity", f"{results['passive_cooling_capacity']:.2f}", "kW"))
        self.rdh_results_tree.insert("", tk.END, values=("Passive Percentage", f"{results['passive_percentage']:.2f}", "%"))
        self.rdh_results_tree.insert("", tk.END, values=("Thermal Coverage", f"{results['thermal_coverage']:.2f}", "%"))
        self.rdh_results_tree.insert("", tk.END, values=("Water Velocity", f"{results['water_velocity']:.2f}", "m/s"))
        self.rdh_results_tree.insert("", tk.END, values=("Air Velocity", f"{results['air_velocity']:.2f}", "m/s"))
        self.rdh_results_tree.insert("", tk.END, values=("Fan Power", f"{results['fan_power']:.3f}", "kW"))
    
    def update_system_results(self, results):
        """Update the system results tree."""
        system_perf = results["system_performance"]
        
        # Clear existing data
        for item in self.system_results_tree.get_children():
            self.system_results_tree.delete(item)
        
        # Add new data
        self.system_results_tree.insert("", tk.END, values=("Heat Load", f"{results['input_parameters'].heat_load:.2f}", "kW"))
        self.system_results_tree.insert("", tk.END, values=("Thermosiphon Capacity", f"{system_perf['thermosiphon_capacity']:.2f}", "kW"))
        self.system_results_tree.insert("", tk.END, values=("Heat Pipe Capacity", f"{system_perf['heat_pipe_capacity']:.2f}", "kW"))
        self.system_results_tree.insert("", tk.END, values=("PCM Buffer Capacity", f"{system_perf['pcm_buffer_capacity']:.2f}", "kWh"))
        self.system_results_tree.insert("", tk.END, values=("AHU Dissipation", f"{system_perf['ahu_dissipation']:.2f}", "kW"))
        self.system_results_tree.insert("", tk.END, values=("Thermal Load Coverage", f"{system_perf['thermal_coverage']:.2f}", "%"))
        self.system_results_tree.insert("", tk.END, values=("Buffer Time", f"{system_perf['buffer_time']:.2f}", "min"))
        self.system_results_tree.insert("", tk.END, values=("Conventional PUE", "1.67", ""))
        self.system_results_tree.insert("", tk.END, values=("Passive System PUE", "1.06", ""))
        self.system_results_tree.insert("", tk.END, values=("Energy Savings", f"{system_perf['energy_savings']:.2f}", "MWh/year"))
        self.system_results_tree.insert("", tk.END, values=("Cost Savings", f"{system_perf['cost_savings']:.2f}", "$/year"))
        self.system_results_tree.insert("", tk.END, values=("CO₂ Reduction", f"{system_perf['co2_reduction']:.2f}", "tonnes/year"))
        self.system_results_tree.insert("", tk.END, values=("ROI Period", f"{system_perf['roi_period']:.2f}", "years"))
    
    def display_performance_charts(self):
        """Display system performance charts."""
        # Create figure
        fig = self.calculator.plot_performance()
        
        # Clear previous chart if exists
        for widget in self.chart_canvas_frame.winfo_children():
            widget.destroy()
        
        # Create canvas for matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=self.chart_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_parameters(self):
        """Update the parameters object from the input fields."""
        try:
            self.params.heat_load = self.heat_load_var.get()
            self.params.ambient_temp = self.ambient_temp_var.get()
            self.params.height = self.height_var.get()
            self.params.cold_pipe_diameter = self.cold_pipe_diameter_var.get()
            self.params.hot_pipe_diameter = self.hot_pipe_diameter_var.get()
            self.params.cold_temp = self.cold_temp_var.get()
            self.params.hot_temp = self.hot_temp_var.get()
            self.params.heat_pipe_count = self.heat_pipe_count_var.get()
            self.params.heat_pipe_diameter = self.heat_pipe_diameter_var.get()
            self.params.pcm_volume = self.pcm_volume_var.get()
            self.params.ahu_surface_area = self.ahu_surface_area_var.get()
            self.params.dimple_density = self.dimple_density_var.get()
            
            # Update calculator
            self.calculator = PassiveCoolingCalculator(self.params)
            
            return True
        except Exception as e:
            messagebox.showerror("Parameter Error", f"Error updating parameters: {str(e)}")
            return False
    
    def update_rdh_parameters(self):
        """Update the RDHx parameters dictionary from the input fields."""
        try:
            self.rdh_params["server_heat_load"] = self.rdh_heat_load_var.get()
            self.rdh_params["inlet_water_temp"] = self.rdh_inlet_water_var.get()
            self.rdh_params["outlet_water_temp"] = self.rdh_outlet_water_var.get()
            self.rdh_params["inlet_air_temp"] = self.rdh_inlet_air_var.get()
            self.rdh_params["outlet_air_temp"] = self.rdh_outlet_air_var.get()
            self.rdh_params["water_flow_rate"] = self.rdh_water_flow_var.get()
            self.rdh_params["air_flow_rate"] = self.rdh_air_flow_var.get()
            self.rdh_params["fan_count"] = self.rdh_fan_count_var.get()
            self.rdh_params["coil_rows"] = self.rdh_coil_rows_var.get()
            self.rdh_params["door_width"] = self.rdh_door_width_var.get()
            self.rdh_params["door_height"] = self.rdh_door_height_var.get()
            
            # Update calculator
            self.rdh_calculator = RearDoorCalculator(self.rdh_params)
            
            return True
        except Exception as e:
            messagebox.showerror("Parameter Error", f"Error updating RDHx parameters: {str(e)}")
            return False
    
    def calculate(self):
        """Calculate all the results and update the UI."""
        if not self.update_parameters():
            return
        
        try:
            # Calculate results
            results = self.calculator.calculate_all()
            
            # Update main summary
            self.update_main_summary(results)
            
            # Update individual tabs
            self.update_thermosiphon_results(results)
            self.update_heat_pipe_results(results)
            self.update_pcm_results(results)
            self.update_dimple_results(results)
            self.update_system_results(results)
            
            # Display performance charts
            self.display_performance_charts()
            
            # Also calculate RDHx if we need to show both together
            self.calculate_rdh(show_message=False)
            
            messagebox.showinfo("Calculation Complete", "All calculations have completed successfully.")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {str(e)}")
    
    def calculate_rdh(self, show_message=True):
        """Calculate RDHx results and update the UI."""
        if not self.update_rdh_parameters():
            return
        
        try:
            # Calculate RDHx results
            results = self.rdh_calculator.calculate()
            
            # Update RDHx results
            self.update_rdh_results(results)
            
            if show_message:
                messagebox.showinfo("Calculation Complete", "RDHx calculations have completed successfully.")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during RDHx calculation: {str(e)}")
    
    def validate_parameters(self):
        """Validate all parameters and show results."""
        if not self.update_parameters():
            return
        
        try:
            # Calculate results
            results = self.calculator.calculate_all()
            validations = results["validations"]
            
            # Create validation report
            report = "Parameter Validation Results:\n\n"
            for param, status in validations.items():
                report += f"{param}: {status}\n"
            
            # Add recommendations if needed
            issues = [param for param, status in validations.items() if status != "OK"]
            if issues:
                report += "\nRecommendations:\n"
                for issue in issues:
                    if issue == "height":
                        report += "- Increase height differential to at least 5m\n"
                    elif issue == "temp_diff":
                        report += "- Adjust cold/hot water temperatures for 5-20°C difference\n"
                    elif issue == "flow_velocity":
                        report += "- Adjust pipe diameters to achieve 0.1-2.0 m/s flow velocity\n"
                    elif issue == "heat_pipe_count":
                        report += "- Use 50-200 heat pipes for optimal performance\n"
                    elif issue == "pcm_volume":
                        report += "- Increase PCM volume to 0.3-2.0 m³\n"
                    elif issue == "capacity_coverage":
                        report += "- System coverage is insufficient, consider increasing heat pipe count\n"
            else:
                report += "\nAll parameters are within recommended ranges."
            
            # Show validation results
            messagebox.showinfo("Parameter Validation", report)
        except Exception as e:
            messagebox.showerror("Validation Error", f"Error during validation: {str(e)}")
    
    def reset_parameters(self):
        """Reset parameters to default values."""
        if messagebox.askyesno("Reset Parameters", "Are you sure you want to reset all parameters to default values?"):
            # Reset main parameters
            self.params = InputParameters()
            
            # Update UI variables
            self.heat_load_var.set(self.params.heat_load)
            self.ambient_temp_var.set(self.params.ambient_temp)
            self.height_var.set(self.params.height)
            self.cold_pipe_diameter_var.set(self.params.cold_pipe_diameter)
            self.hot_pipe_diameter_var.set(self.params.hot_pipe_diameter)
            self.cold_temp_var.set(self.params.cold_temp)
            self.hot_temp_var.set(self.params.hot_temp)
            self.heat_pipe_count_var.set(self.params.heat_pipe_count)
            self.heat_pipe_diameter_var.set(self.params.heat_pipe_diameter)
            self.pcm_volume_var.set(self.params.pcm_volume)
            self.ahu_surface_area_var.set(self.params.ahu_surface_area)
            self.dimple_density_var.set(self.params.dimple_density)
            
            # Reset RDHx parameters
            self.rdh_params = RearDoorCalculator().params
            
            # Update RDHx UI variables
            self.rdh_heat_load_var.set(self.rdh_params["server_heat_load"])
            self.rdh_inlet_water_var.set(self.rdh_params["inlet_water_temp"])
            self.rdh_outlet_water_var.set(self.rdh_params["outlet_water_temp"])
            self.rdh_inlet_air_var.set(self.rdh_params["inlet_air_temp"])
            self.rdh_outlet_air_var.set(self.rdh_params["outlet_air_temp"])
            self.rdh_water_flow_var.set(self.rdh_params["water_flow_rate"])
            self.rdh_air_flow_var.set(self.rdh_params["air_flow_rate"])
            self.rdh_fan_count_var.set(self.rdh_params["fan_count"])
            self.rdh_coil_rows_var.set(self.rdh_params["coil_rows"])
            self.rdh_door_width_var.set(self.rdh_params["door_width"])
            self.rdh_door_height_var.set(self.rdh_params["door_height"])
            
            # Reset calculators
            self.calculator = PassiveCoolingCalculator(self.params)
            self.rdh_calculator = RearDoorCalculator(self.rdh_params)
            
            messagebox.showinfo("Reset Complete", "All parameters have been reset to default values.")
    
    def new_project(self):
        """Reset to a new project."""
        self.reset_parameters()
        messagebox.showinfo("New Project", "Created a new project with default parameters.")
    
    def open_project(self):
        """Open a saved project file."""
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Load main parameters
            if 'main_params' in data:
                params_dict = data['main_params']
                self.params = InputParameters()
                
                # Update parameters from saved data
                for key, value in params_dict.items():
                    if hasattr(self.params, key):
                        setattr(self.params, key, value)
                
                # Update UI variables
                self.heat_load_var.set(self.params.heat_load)
                self.ambient_temp_var.set(self.params.ambient_temp)
                self.height_var.set(self.params.height)
                self.cold_pipe_diameter_var.set(self.params.cold_pipe_diameter)
                self.hot_pipe_diameter_var.set(self.params.hot_pipe_diameter)
                self.cold_temp_var.set(self.params.cold_temp)
                self.hot_temp_var.set(self.params.hot_temp)
                self.heat_pipe_count_var.set(self.params.heat_pipe_count)
                self.heat_pipe_diameter_var.set(self.params.heat_pipe_diameter)
                self.pcm_volume_var.set(self.params.pcm_volume)
                self.ahu_surface_area_var.set(self.params.ahu_surface_area)
                self.dimple_density_var.set(self.params.dimple_density)
            
            # Load RDHx parameters
            if 'rdh_params' in data:
                self.rdh_params = data['rdh_params']
                
                # Update RDHx UI variables
                self.rdh_heat_load_var.set(self.rdh_params["server_heat_load"])
                self.rdh_inlet_water_var.set(self.rdh_params["inlet_water_temp"])
                self.rdh_outlet_water_var.set(self.rdh_params["outlet_water_temp"])
                self.rdh_inlet_air_var.set(self.rdh_params["inlet_air_temp"])
                self.rdh_outlet_air_var.set(self.rdh_params["outlet_air_temp"])
                self.rdh_water_flow_var.set(self.rdh_params["water_flow_rate"])
                self.rdh_air_flow_var.set(self.rdh_params["air_flow_rate"])
                self.rdh_fan_count_var.set(self.rdh_params["fan_count"])
                self.rdh_coil_rows_var.set(self.rdh_params["coil_rows"])
                self.rdh_door_width_var.set(self.rdh_params["door_width"])
                self.rdh_door_height_var.set(self.rdh_params["door_height"])
            
            # Reset calculators
            self.calculator = PassiveCoolingCalculator(self.params)
            self.rdh_calculator = RearDoorCalculator(self.rdh_params)
            
            # Run calculations with loaded data
            self.calculate()
            
            messagebox.showinfo("Project Loaded", f"Project loaded successfully from {file_path}")
        except Exception as e:
            messagebox.showerror("Error Loading Project", f"Error loading project: {str(e)}")
    
    def save_project(self):
        """Save the current project."""
        # Save the current project to last used file path if available
        if hasattr(self, 'last_save_path') and self.last_save_path:
            self.save_project_to_file(self.last_save_path)
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Save the current project to a new file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        self.save_project_to_file(file_path)
    
    def save_project_to_file(self, file_path):
        """Save the current project to the specified file."""
        try:
            # Update parameters from UI
            self.update_parameters()
            self.update_rdh_parameters()
            
            # Create data dictionary
            data = {
                'main_params': asdict(self.params),
                'rdh_params': self.rdh_params
            }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            # Store the path for future saves
            self.last_save_path = file_path
            
            messagebox.showinfo("Project Saved", f"Project saved successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error Saving Project", f"Error saving project: {str(e)}")
    
    def import_from_solid_edge(self):
        """Import parameters from Solid Edge."""
        try:
            file_path = filedialog.askopenfilename(
                title="Select Solid Edge File",
                filetypes=[("Solid Edge Files", "*.par;*.asm"), ("All Files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Call the import function from the calculator module
            imported_params = read_from_solid_edge(file_path)
            
            if imported_params:
                # Update parameters
                self.params = imported_params
                
                # Update UI
                self.heat_load_var.set(self.params.heat_load)
                self.ambient_temp_var.set(self.params.ambient_temp)
                self.height_var.set(self.params.height)
                self.cold_pipe_diameter_var.set(self.params.cold_pipe_diameter)
                self.hot_pipe_diameter_var.set(self.params.hot_pipe_diameter)
                self.cold_temp_var.set(self.params.cold_temp)
                self.hot_temp_var.set(self.params.hot_temp)
                self.heat_pipe_count_var.set(self.params.heat_pipe_count)
                self.heat_pipe_diameter_var.set(self.params.heat_pipe_diameter)
                self.pcm_volume_var.set(self.params.pcm_volume)
                self.ahu_surface_area_var.set(self.params.ahu_surface_area)
                self.dimple_density_var.set(self.params.dimple_density)
                
                # Reset calculator
                self.calculator = PassiveCoolingCalculator(self.params)
                
                messagebox.showinfo("Import Successful", f"Parameters imported from {file_path}")
                
                # Run calculations with imported data
                self.calculate()
            else:
                messagebox.showwarning("Import Warning", "No parameters were imported. Using defaults.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing from Solid Edge: {str(e)}")
    
    def export_to_solid_edge(self):
        """Export results to Solid Edge."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save to Solid Edge",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Update parameters and calculate
            self.update_parameters()
            results = self.calculator.calculate_all()
            
            # Call the export function from the calculator module
            write_to_solid_edge(results, file_path)
            
            messagebox.showinfo("Export Successful", f"Results exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting to Solid Edge: {str(e)}")
    
    def export_report(self):
        """Export a detailed report of all results."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Report",
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Update parameters and calculate
            self.update_parameters()
            results = self.calculator.calculate_all()
            
            # Create report content
            report = "PASSIVE COOLING SYSTEM ANALYSIS REPORT\n"
            report += "=" * 50 + "\n\n"
            
            # Date and time
            from datetime import datetime
            report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Input parameters
            report += "INPUT PARAMETERS\n"
            report += "-" * 20 + "\n"
            for key, value in asdict(results["input_parameters"]).items():
                report += f"{key}: {value}\n"
            report += "\n"
            
            # Thermosiphon results
            report += "THERMOSIPHON PERFORMANCE\n"
            report += "-" * 20 + "\n"
            for key, value in results["thermosiphon"].items():
                report += f"{key}: {value:.4f}\n"
            report += "\n"
            
            # Heat pipe results
            report += "HEAT PIPE PERFORMANCE\n"
            report += "-" * 20 + "\n"
            for key, value in results["heat_pipes"].items():
                report += f"{key}: {value:.4f}\n"
            report += "\n"
            
            # PCM results
            report += "PCM PERFORMANCE\n"
            report += "-" * 20 + "\n"
            for key, value in results["pcm"].items():
                report += f"{key}: {value:.4f}\n"
            report += "\n"
            
            # Dimpled surface results
            report += "DIMPLED SURFACE PERFORMANCE\n"
            report += "-" * 20 + "\n"
            for key, value in results["dimpled_surface"].items():
                report += f"{key}: {value:.4f}\n"
            report += "\n"
            
            # System performance results
            report += "SYSTEM PERFORMANCE\n"
            report += "-" * 20 + "\n"
            for key, value in results["system_performance"].items():
                report += f"{key}: {value:.4f}\n"
            report += "\n"
            
            # Validation results
            report += "PARAMETER VALIDATION\n"
            report += "-" * 20 + "\n"
            for key, value in results["validations"].items():
                report += f"{key}: {value}\n"
            report += "\n"
            
            # Save to file
            with open(file_path, 'w') as f:
                f.write(report)
            
            messagebox.showinfo("Report Exported", f"Report exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting report: {str(e)}")
    
    def sensitivity_analysis(self):
        """Perform sensitivity analysis on key parameters."""
        # Create a new window for sensitivity analysis
        sensitivity_window = tk.Toplevel(self.root)
        sensitivity_window.title("Sensitivity Analysis")
        sensitivity_window.geometry("800x600")
        
        # Parameters to analyze
        parameters = [
            ("Height Differential", "height", 5, 15, 1),
            ("Heat Pipe Count", "heat_pipe_count", 50, 200, 10),
            ("PCM Volume", "pcm_volume", 0.2, 1.0, 0.1),
            ("Heat Load", "heat_load", 50, 150, 10)
        ]
        
        # Create notebook for parameter tabs
        notebook = ttk.Notebook(sensitivity_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a tab for each parameter
        for param_name, param_id, min_val, max_val, step in parameters:
            # Create tab
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=param_name)
            
            # Create matplotlib figure
            fig = plt.Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Create x values
            x_values = np.arange(min_val, max_val + step, step)
            y_values = []
            
            # Calculate for each x value
            for x in x_values:
                # Create a copy of parameters
                params_copy = InputParameters(**asdict(self.params))
                
                # Update the parameter
                setattr(params_copy, param_id, x)
                
                # Calculate results
                calculator = PassiveCoolingCalculator(params_copy)
                results = calculator.calculate_all()
                
                # Get key metric
                if param_id == "heat_load":
                    y_values.append(results["system_performance"]["roi_period"])
                else:
                    y_values.append(results["system_performance"]["thermal_coverage"])
            
            # Plot results
            ax.plot(x_values, y_values, 'bo-')
            
            # Set labels
            ax.set_xlabel(param_name)
            if param_id == "heat_load":
                ax.set_ylabel("ROI Period (years)")
                ax.set_title(f"Effect of {param_name} on ROI Period")
            else:
                ax.set_ylabel("Thermal Coverage (%)")
                ax.set_title(f"Effect of {param_name} on Thermal Coverage")
            
            ax.grid(True)
            
            # Add the plot to the tab
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def optimization(self):
        """Perform parameter optimization."""
        messagebox.showinfo("Optimization", "Parameter optimization feature is under development.")
    
    def generate_reports(self):
        """Generate comprehensive reports."""
        messagebox.showinfo("Reports", "Report generation feature is under development.")
    
    def show_documentation(self):
        """Show application documentation."""
        doc_text = """
        Thermal System Calculator Documentation
        
        This application calculates the performance of a passive cooling system
        using thermosiphon, heat pipes, phase change materials, and dimpled surfaces.
        
        How to use:
        1. Enter system parameters in the Main Parameters tab
        2. Click Calculate to compute all results
        3. View detailed results in each component's tab
        4. Export reports or save your project for later use
        
        Key features:
        - Thermosiphon performance calculation
        - Heat pipe system design
        - PCM thermal storage analysis
        - Dimpled surface heat transfer enhancement
        - Rear door heat exchanger analysis
        - System-level performance metrics
        - Parameter validation
        - Sensitivity analysis
        
        For more information, contact the development team.
        """
        
        # Create documentation window
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x400")
        
        # Add text widget
        text = tk.Text(doc_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(text, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # Insert documentation text
        text.insert(tk.END, doc_text)
        text.config(state=tk.DISABLED)
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
        Thermal System Calculator v1.0
        
        A comprehensive tool for designing and analyzing
        passive cooling systems for data centers.
        
        Features include thermosiphon calculations, heat pipe design,
        PCM storage analysis, and system performance metrics.
        
        Developed as part of innovative cooling system R&D.
        """
        
        messagebox.showinfo("About", about_text)


def main():
    root = tk.Tk()
    app = ThermalCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

