# Data Center Cooling Calculator: System Architecture

## 1. System Overview

This architecture defines a comprehensive cooling calculator for data center enclosures that consolidates currently separate tools (My Coil, Fan Select, ROI calculator) into a unified platform. The system is designed to be:

- **Simple to use**: Requiring minimal inputs (cooling required, room temperature, outlet temperature, supply water temperature)
- **Technically comprehensive**: Providing detailed engineering calculations
- **Commercially valuable**: Offering ROI, TCO, and environmental impact assessments
- **Regionally aware**: Adapting to different global standards and conditions

## 2. Core Architecture

![System Architecture Diagram](https://link-that-would-go-to-diagram)

```
DataCenterCoolingCalculator/
├── core/                        # Core system functionality
├── models/                      # Component models and specifications
├── calculations/                # Engineering calculations
├── commercial/                  # Business and commercial calculations
├── analytics/                   # Usage and trends analytics
├── validation/                  # Testing and validation
├── ui/                          # User interfaces (web, desktop)
└── utils/                       # Utility functions
```

## 3. Major Components

### 3.1 Core Engine

The heart of the system: processes inputs, manages calculation flow, and produces outputs.

```python
# core/engine.py
class CalculationEngine:
    def __init__(self, product_database, regional_settings=None):
        self.products = product_database
        self.regional_settings = regional_settings or default_settings()
        
    def calculate(self, cooling_kw, room_temp, desired_temp, water_temp, **kwargs):
        """Main calculation method requiring only the essential inputs."""
        # Select appropriate product
        product = self._select_product(cooling_kw, kwargs.get('rack_type'))
        
        # Create system components
        heat_exchanger = self._create_heat_exchanger(product, kwargs)
        fan_system = self._create_fan_system(product, kwargs)
        piping = self._create_piping_config(kwargs)
        
        # Calculate technical performance
        performance = self._calculate_technical_performance(
            heat_exchanger, fan_system, piping,
            cooling_kw, room_temp, desired_temp, water_temp, 
            **kwargs
        )
        
        # Calculate commercial aspects if requested
        if kwargs.get('include_commercial', True):
            performance['commercial'] = self._calculate_commercial_aspects(
                performance, kwargs
            )
            
        return performance
```

### 3.2 Heat Exchanger Module

Handles thermal calculations for the heat exchanger, implementing industry-standard equations.

```python
# models/heat_exchanger.py
class HeatExchanger:
    def __init__(self, coil_geometry, fluid_type='water', glycol_percentage=0):
        self.geometry = coil_geometry
        self.fluid = self._get_fluid_properties(fluid_type, glycol_percentage)
        
    def calculate_performance(self, cooling_kw, supply_temp, return_temp=None, flow_rate=None):
        """Calculate heat exchanger performance.
        
        Must provide either return_temp or flow_rate.
        """
        # Implement LMTD or ε-NTU method based on inputs
        if flow_rate is None and return_temp is not None:
            # Q = ṁ × cp × ΔT, solve for ṁ (flow_rate)
            flow_rate = self._calculate_flow_rate(cooling_kw, supply_temp, return_temp)
        elif return_temp is None and flow_rate is not None:
            # Q = ṁ × cp × ΔT, solve for ΔT, then find return_temp
            return_temp = self._calculate_return_temp(cooling_kw, supply_temp, flow_rate)
        else:
            raise ValueError("Must provide either return_temp or flow_rate")
            
        # Calculate pressure drop through coil
        pressure_drop = self._calculate_pressure_drop(flow_rate)
        
        return {
            'cooling_capacity': cooling_kw,
            'flow_rate': flow_rate,
            'supply_temp': supply_temp,
            'return_temp': return_temp,
            'pressure_drop': pressure_drop
        }
    
    def recommend_valve(self, flow_rate):
        """Recommend optimal valve based on flow rate."""
        # Logic to select from available valves based on flow rate
        # Consider standard 2-way valve vs EPIV as mentioned in transcript
```

### 3.3 Fan Module

Calculates fan performance, power consumption, and noise levels.

```python
# models/fan.py
class FanSystem:
    def __init__(self, fan_specs, controller_specs, num_fans=1):
        self.fan_specs = fan_specs
        self.controller = controller_specs
        self.num_fans = num_fans
        
    def calculate_performance(self, air_flow_required, static_pressure, voltage=230):
        """Calculate fan performance parameters."""
        # Apply fan laws to determine operating point
        fan_speed = self._calculate_required_speed(air_flow_required, static_pressure)
        
        # Adjust for voltage (208V US vs 230V EU as mentioned in transcript)
        adjusted_power = self._adjust_power_for_voltage(fan_speed, voltage)
        
        # Calculate noise level
        noise = self._calculate_noise(fan_speed)
        
        return {
            'fan_speed_percentage': fan_speed,
            'air_flow': air_flow_required,
            'static_pressure': static_pressure,
            'power_consumption': adjusted_power,
            'noise_level': noise
        }
```

### 3.4 Piping and Pressure Module

Handles fluid dynamics calculations for piping systems.

```python
# models/piping.py
class PipingSystem:
    def __init__(self, configuration='bottom_fed', pipe_length=3.7, pipe_diameter=25):
        self.configuration = configuration
        self.length = pipe_length  # meters
        self.diameter = pipe_diameter  # mm
        
    def calculate_pressure_drop(self, flow_rate, fluid_properties):
        """Calculate pressure drop through piping system."""
        # Base pressure drop for straight pipe
        straight_pressure_drop = self._calculate_straight_pipe_drop(
            flow_rate, self.length, self.diameter, fluid_properties
        )
        
        # Additional pressure drop for bends
        if self.configuration == 'top_fed':
            # Add pressure drop for 180° bend as mentioned in transcript
            bend_pressure_drop = self._calculate_bend_pressure_drop(
                flow_rate, 180, self.diameter, fluid_properties
            )
        else:
            bend_pressure_drop = 0
            
        # Add valve pressure drop
        valve_pressure_drop = self._calculate_valve_pressure_drop(flow_rate)
        
        return {
            'total_pressure_drop': straight_pressure_drop + bend_pressure_drop + valve_pressure_drop,
            'straight_pipe_drop': straight_pressure_drop,
            'bend_pressure_drop': bend_pressure_drop,
            'valve_pressure_drop': valve_pressure_drop
        }
```

### 3.5 Commercial Module

Calculates business metrics like TCO, ROI, and environmental impact.

```python
# commercial/calculator.py
class CommercialCalculator:
    def __init__(self, energy_costs, carbon_factors):
        self.energy_costs = energy_costs
        self.carbon_factors = carbon_factors
        
    def calculate_tco(self, technical_performance, operating_hours, lifespan):
        """Calculate Total Cost of Ownership."""
        # Calculate energy consumption
        annual_energy = self._calculate_annual_energy(
            technical_performance, operating_hours
        )
        
        # Calculate costs
        energy_cost = annual_energy * self.energy_costs['electricity'] * lifespan
        capital_cost = self._estimate_capital_cost(technical_performance)
        maintenance_cost = self._estimate_maintenance_cost(technical_performance) * lifespan
        
        return {
            'total_cost': capital_cost + energy_cost + maintenance_cost,
            'capital_cost': capital_cost,
            'energy_cost': energy_cost,
            'maintenance_cost': maintenance_cost,
            'payback_period': self._calculate_payback_period(capital_cost, annual_energy)
        }
        
    def calculate_environmental_impact(self, technical_performance, operating_hours, lifespan):
        """Calculate environmental impact metrics."""
        # Calculate carbon emissions
        annual_energy = self._calculate_annual_energy(technical_performance, operating_hours)
        annual_carbon = annual_energy * self.carbon_factors['electricity']
        lifetime_carbon = annual_carbon * lifespan
        
        # Convert to equivalents (trees, cars) as mentioned in transcript
        tree_equivalent = lifetime_carbon * 0.039  # Trees needed to absorb carbon
        car_equivalent = lifetime_carbon / 4.6  # Equivalent cars removed
        
        return {
            'annual_carbon': annual_carbon,
            'lifetime_carbon': lifetime_carbon,
            'tree_equivalent': tree_equivalent,
            'car_equivalent': car_equivalent
        }
```

## 4. Key Industry Standard Equations

### 4.1 Heat Transfer Equations

```python
# calculations/thermal.py

def heat_transfer_rate(mass_flow, specific_heat, temp_diff):
    """Q = ṁ × cp × ΔT"""
    return mass_flow * specific_heat * temp_diff

def log_mean_temp_difference(hot_in, hot_out, cold_in, cold_out):
    """Calculate LMTD for heat exchanger calculations."""
    delta_t1 = hot_in - cold_out
    delta_t2 = hot_out - cold_in
    
    if abs(delta_t1 - delta_t2) < 0.001:
        return delta_t1  # Avoid division by zero
    
    return (delta_t1 - delta_t2) / math.log(delta_t1 / delta_t2)

def effectiveness_ntu_method(c_min, c_max, ua):
    """Calculate heat exchanger effectiveness using ε-NTU method.
    
    This is used when not all inlet/outlet temperatures are known.
    """
    c_ratio = c_min / c_max
    ntu = ua / c_min
    
    # For cross-flow heat exchanger with both fluids unmixed
    term1 = 1 - math.exp(-ntu * c_ratio**(-0.22))
    effectiveness = 1 - math.exp(-term1 / c_ratio)
    
    return effectiveness
```

### 4.2 Fluid Dynamics Equations

```python
# calculations/fluid_dynamics.py

def reynolds_number(velocity, diameter, density, viscosity):
    """Calculate Reynolds number to determine flow regime."""
    return (velocity * diameter * density) / viscosity

def darcy_friction_factor(reynolds, relative_roughness):
    """Calculate Darcy friction factor for pressure drop calculations."""
    if reynolds < 2300:
        # Laminar flow
        return 64 / reynolds
    else:
        # Turbulent flow - Colebrook equation (implicit)
        # Using approximate explicit form for simplicity
        return 0.25 / (math.log10(relative_roughness/3.7 + 5.74/reynolds**0.9))**2

def pressure_drop_pipe(friction_factor, length, diameter, density, velocity):
    """Calculate pressure drop in straight pipe."""
    return friction_factor * (length/diameter) * (density * velocity**2 / 2)

def pressure_drop_fitting(k_factor, density, velocity):
    """Calculate pressure drop in fittings (valves, bends, etc.)."""
    return k_factor * (density * velocity**2 / 2)
```

### 4.3 Fan Performance Equations

```python
# calculations/airflow.py

def fan_laws_flow(flow1, speed1, speed2):
    """Q₂ = Q₁ × (N₂/N₁)"""
    return flow1 * (speed2 / speed1)

def fan_laws_pressure(pressure1, speed1, speed2):
    """P₂ = P₁ × (N₂/N₁)²"""
    return pressure1 * ((speed2 / speed1) ** 2)

def fan_laws_power(power1, speed1, speed2):
    """W₂ = W₁ × (N₂/N₁)³"""
    return power1 * ((speed2 / speed1) ** 3)

def required_air_flow(cooling_capacity, air_density, specific_heat, temp_diff):
    """Calculate required air flow for given cooling capacity."""
    return cooling_capacity / (air_density * specific_heat * temp_diff)
```

### 4.4 Energy Efficiency Equations

```python
# calculations/efficiency.py

def coefficient_of_performance(cooling_output, power_input):
    """Calculate COP (Coefficient of Performance)."""
    return cooling_output / power_input

def energy_efficiency_ratio(cooling_btu_per_hour, power_watts):
    """Calculate EER (Energy Efficiency Ratio)."""
    return cooling_btu_per_hour / power_watts

def power_usage_effectiveness(total_facility_energy, it_equipment_energy):
    """Calculate PUE (Power Usage Effectiveness)."""
    return total_facility_energy / it_equipment_energy

def seasonal_energy_efficiency_ratio(cooling_btu_seasonal, energy_watt_hours_seasonal):
    """Calculate SEER (Seasonal Energy Efficiency Ratio)."""
    return cooling_btu_seasonal / energy_watt_hours_seasonal
```

## 5. Regional Standards Implementation

```python
# core/regional_standards.py

# Define regional standards and specifications
REGIONAL_STANDARDS = {
    'global': {
        'ashrae': {
            'class_a1': {
                'temp_recommended': {'min': 18, 'max': 27},  # °C
                'humidity_recommended': {'min': 40, 'max': 60},  # % RH
            },
            # Other ASHRAE classes...
        }
    },
    
    'europe': {
        'energy_costs': {'electricity': 0.20},  # €/kWh (example)
        'carbon_factors': {'electricity': 0.275},  # kg CO2/kWh (EU average)
        'efficiency_metric': 'SEER',  # Seasonal Energy Efficiency Ratio
        'regulations': ['EU Code of Conduct for Data Centers', 'EN 50600'],
        'default_voltage': 230,
        'default_fluid': 'water',
    },
    
    'north_america': {
        'energy_costs': {'electricity': 0.15},  # $/kWh (example)
        'carbon_factors': {'electricity': 0.417},  # kg CO2/kWh (US average)
        'efficiency_metric': 'IEER',  # Integrated Energy Efficiency Ratio
        'regulations': ['ASHRAE 90.4', 'ENERGY STAR for Data Centers'],
        'default_voltage': 208,
        'default_fluid': 'water',
        'preferred_units': 'imperial',
    },
    
    'nordic': {
        'energy_costs': {'electricity': 0.10},  # €/kWh (example)
        'carbon_factors': {'electricity': 0.028},  # kg CO2/kWh (Norway example)
        'default_fluid': 'propylene_glycol',  # As mentioned in transcript
        'default_glycol_percentage': 30,
        'free_cooling_potential': 'high',
    },
    
    'asia_pacific': {
        'singapore': {
            'energy_costs': {'electricity': 0.18},  # S$/kWh (example)
            'carbon_factors': {'electricity': 0.408},  # kg CO2/kWh
            'regulations': ['SS 564', 'Green Mark for Data Centers'],
            'ambient_temp': {'min': 25, 'max': 32},
            'humidity': {'min': 70, 'max': 90},
            'dew_point_concerns': 'high',
            'water_min_temp': 18,  # As mentioned in transcript
        },
        # Other APAC regions...
    }
}

def get_regional_settings(region, subregion=None):
    """Get settings for specific region with appropriate fallbacks."""
    settings = copy.deepcopy(REGIONAL_STANDARDS['global'])
    
    if region in REGIONAL_STANDARDS:
        _deep_update(settings, REGIONAL_STANDARDS[region])
        
        if subregion and subregion in REGIONAL_STANDARDS[region]:
            _deep_update(settings, REGIONAL_STANDARDS[region][subregion])
            
    return settings

def adjust_for_altitude(base_calculations, altitude):
    """Adjust calculations for installation altitude."""
    if altitude <= 0:
        return base_calculations  # No adjustment needed
    
    # Air density correction
    # ρ = ρ₀ × exp(-g × M × h / (R × T))
    air_density_factor = math.exp(-9.81 * 0.0289644 * altitude / (8.31447 * 288.15))
    
    # Adjust air-side calculations
    base_calculations['air_side']['air_density'] *= air_density_factor
    
    # Recalculate fan performance with adjusted air density
    # Adjust cooling capacity for thinner air
    
    return base_calculations
```

## 6. User Interface Design

### 6.1 Web Interface (Flask/React)

```python
# ui/web/app.py
from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """API endpoint for calculation."""
    data = request.get_json()
    
    # Extract required parameters
    cooling_kw = data.get('cooling_kw')
    room_temp = data.get('room_temp')
    desired_temp = data.get('desired_temp')
    water_temp = data.get('water_temp')
    
    # Validate required inputs
    if not all([cooling_kw, room_temp, desired_temp, water_temp]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Pass additional parameters as kwargs
    kwargs = {k: v for k, v in data.items() 
              if k not in ['cooling_kw', 'room_temp', 'desired_temp', 'water_temp']}
    
    # Perform calculation
    calculator = get_calculator_instance()
    result = calculator.calculate(cooling_kw, room_temp, desired_temp, water_temp, **kwargs)
    
    return jsonify(result)
```

### 6.2 Desktop Interface (PyQt)

```python
# ui/desktop/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Center Cooling Calculator")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create input fields
        self.cooling_input = self._create_input_field("Cooling Required (kW):", layout)
        self.room_temp_input = self._create_input_field("Room Temperature (°C):", layout)
        self.desired_temp_input = self._create_input_field("Desired Room Temperature (°C):", layout)
        self.water_temp_input = self._create_input_field("Supply Water Temperature (°C):", layout)
        
        # Create calculate button
        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculate)
        layout.addWidget(calculate_button)
        
        # Results area
        self.results_area = QLabel("Results will appear here")
        layout.addWidget(self.results_area)
    
    def _create_input_field(self, label_text, layout):
        """Helper to create labeled input field."""
        layout.addWidget(QLabel(label_text))
        input_field = QLineEdit()
        layout.addWidget(input_field)
        return input_field
    
    def calculate(self):
        """Perform calculation and display results."""
        # Get input values
        cooling_kw = float(self.cooling_input.text())
        room_temp = float(self.room_temp_input.text())
        desired_temp = float(self.desired_temp_input.text())
        water_temp = float(self.water_temp_input.text())
        
        # Perform calculation
        calculator = get_calculator_instance()
        result = calculator.calculate(cooling_kw, room_temp, desired_temp, water_temp)
        
        # Display results
        self.results_area.setText(format_results(result))
```

## 7. Analytics and Tracking

```python
# analytics/usage_tracker.py
class UsageTracker:
    def __init__(self, storage_backend):
        self.storage = storage_backend
        
    def track_calculation(self, inputs, results, user_info=None):
        """Track calculation for analytics."""
        # Record calculation with timestamp
        record = {
            'timestamp': datetime.now().isoformat(),
            'inputs': {
                'cooling_kw': inputs.get('cooling_kw'),
                'room_temp': inputs.get('room_temp'),
                'desired_temp': inputs.get('desired_temp'),
                'water_temp': inputs.get('water_temp'),
                'location': inputs.get('location'),
                'altitude': inputs.get('altitude'),
                'fluid_type': inputs.get('fluid_type'),
                'glycol_percentage': inputs.get('glycol_percentage')
            },
            'results': {
                'recommended_product': results.get('product', {}).get('name'),
                'flow_rate': results.get('water_side', {}).get('flow_rate'),
                'valve_type': results.get('valve_recommendation', {}).get('type')
            }
        }
        
        if user_info:
            record['user'] = user_info
            
        self.storage.save_record(record)
        
    def generate_analytics_report(self, time_period=None, region=None):
        """Generate analytics report for specified filters."""
        records = self.storage.get_records(time_period, region)
        
        # Calculate statistics
        stats = {
            'total_calculations': len(records),
            'products_recommended': Counter(r['results']['recommended_product'] for r in records),
            'average_cooling_kw': sum(r['inputs']['cooling_kw'] for r in records) / len(records),
            'fluid_types': Counter(r['inputs']['fluid_type'] for r in records),
            'regions': Counter(r['inputs']['location'] for r in records if r['inputs']['location'])
        }
        
        # Generate regional insights
        regional_insights = self._generate_regional_insights(records)
        
        return {
            'statistics': stats,
            'regional_insights': regional_insights,
            'time_period': time_period,
            'generated_at': datetime.now().isoformat()
        }
        
    def _generate_regional_insights(self, records):
        """Generate insights specific to regions."""
        regions = {}
        
        for record in records:
            location = record['inputs'].get('location')
            if not location:
                continue
                
            if location not in regions:
                regions[location] = {
                    'calculations': 0,
                    'avg_cooling_kw': 0,
                    'fluid_types': Counter(),
                    'water_temps': []
                }
                
            regions[location]['calculations'] += 1
            regions[location]['avg_cooling_kw'] += record['inputs']['cooling_kw']
            regions[location]['fluid_types'][record['inputs']['fluid_type']] += 1
            regions[location]['water_temps'].append(record['inputs']['water_temp'])
        
        # Calculate averages
        for region in regions.values():
            region['avg_cooling_kw'] /= region['calculations']
            region['avg_water_temp'] = sum(region['water_temps']) / len(region['water_temps'])
            region['min_water_temp'] = min(region['water_temps'])
            region['max_water_temp'] = max(region['water_temps'])
            
        return regions
```

## 8. Implementation Strategy

### 8.1 Phase 1: Core Technical Framework
- Implement heat exchanger models and calculations
- Develop unit conversion utilities
- Create validation framework with test cases

### 8.2 Phase 2: System Integration
- Implement fan module
- Add piping and pressure calculations
- Create basic user interface
- Begin validation against real-world data

### 8.3 Phase 3: Commercial Module
- Implement energy and ROI calculations
- Add environmental impact assessment
- Enhance report generation

### 8.4 Phase 4: Regional Adaptations
- Implement regional settings and standards
- Add geographic intelligence
- Support metric and imperial units

### 8.5 Phase 5: Analytics and Deployment
- Implement usage tracking and analytics
- Package for distribution
- Deploy web and desktop interfaces
- Create comprehensive documentation
