# Data Center Cooling Calculator

A comprehensive calculator for data center cooling solutions, specifically designed for ColdLogik rear door heat exchangers.

![Cooling Calculator Banner](docs/images/cooling_calculator_banner.png)

## Overview

The Data Center Cooling Calculator is a powerful tool that provides precise technical calculations for data center cooling systems while remaining accessible to both technical and sales/marketing teams. With just three required inputs, the calculator delivers comprehensive analysis of cooling performance, energy efficiency, and commercial benefits.

### Key Features

- **Simple Inputs**: Calculate cooling performance with just three required inputs
- **Product Selection**: Automatically recommend the optimal cooling solution
- **Technical Analysis**: Detailed heat transfer, airflow, and efficiency calculations
- **Commercial Analysis**: TCO, ROI, and energy savings projections
- **Environmental Impact**: Carbon emissions and sustainability metrics
- **Multiple Interfaces**: API, web, desktop, and command-line interfaces
- **Unit Flexibility**: Toggle between metric and imperial units
- **Regional Adaptation**: Adjust for different global standards and conditions

## Products Supported

- **CL20 Series**: Standard rear door heat exchangers (up to 93kW)
- **CL21 Series**: Passive rear door heat exchangers (up to 29kW)
- **CL23 Series**: High-performance computing solutions (up to 204kW)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/data-center-cooling-calculator.git
   cd data-center-cooling-calculator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run setup:
   ```bash
   python setup.py install
   ```

## Usage

### Basic Usage

```python
from main import DataCenterCoolingCalculator

# Create calculator instance
calculator = DataCenterCoolingCalculator()

# Perform calculation
result = calculator.calculate(
    cooling_kw=50,    # Required cooling capacity in kW
    room_temp=24,     # Room temperature in °C
    desired_temp=22,  # Desired room temperature in °C
    water_temp=15     # Water supply temperature in °C
)

# Print key results
print(f"Recommended product: {result['product']['name']}")
print(f"Water flow rate: {result['water_side']['flow_rate']:.2f} m³/h")
print(f"Fan speed: {result['air_side']['fan_speed_percentage']:.1f}%")
print(f"COP: {result['efficiency']['cop']:.2f}")
```

### Advanced Usage

```python
# More detailed calculation with additional parameters
result = calculator.calculate(
    cooling_kw=60,
    room_temp=25,
    desired_temp=22,
    water_temp=15,
    rack_type="48U800",          # Specific rack type
    fluid_type="propylene_glycol", # Cooling fluid type
    glycol_percentage=30,        # Percentage of glycol in mixture
    units="metric",              # Units system (metric or imperial)
    include_commercial=True      # Include commercial calculations
)

# Get product recommendations
recommendations = calculator.recommend_products(
    cooling_kw=80,
    rack_type="48U800",
    passive_preferred=False
)
```

### Using the API

```python
from clients.python_client import CoolingCalculatorClient

# Create client
client = CoolingCalculatorClient(base_url="http://localhost:5000")

# Get calculation
result = client.calculate(
    cooling_kw=50,
    room_temp=24,
    desired_temp=22,
    water_temp=15
)

# Get recommendations
recommendations = client.recommend_products(cooling_kw=70)
```

## Web Interface

The calculator includes a web interface for easy access:

1. Start the web server:
   ```bash
   python -m ui.web.app
   ```

2. Open your browser and navigate to `http://localhost:8000`

3. Enter your cooling requirements and view the results

![Web Interface](docs/images/web_interface.png)

## API Reference

The calculator exposes a RESTful API:

1. Start the API server:
   ```bash
   python -m api.app
   ```

2. API endpoints:
   - `POST /api/calculate` - Perform cooling calculation
   - `POST /api/recommend` - Get product recommendations
   - `GET /api/products` - Get all available products
   - `GET /api/products/{product_id}` - Get specific product details
   - `POST /api/validate` - Validate input parameters

Full API documentation is available at `/api/docs` when the server is running.

## Commercial Analysis

The calculator provides detailed commercial analysis to help with business decisions:

- **Total Cost of Ownership (TCO)** - Capital, operational, and maintenance costs
- **Return on Investment (ROI)** - Payback period and cost savings
- **Energy Consumption** - Annual energy use and costs
- **Environmental Impact** - Carbon emissions and sustainability metrics

## Configuration

Configuration options can be set in a `config.yaml` file in the root directory:

```yaml
# Example configuration
units: metric
default_location: europe
data_dir: ./data
report_dir: ./reports
```

## Development

### Project Structure

```
DataCenterCoolingCalculator/
├── api/                  # API Interface
├── calculations/         # Engineering calculations
├── clients/              # API clients
├── commercial/           # Business calculations
├── core/                 # Core engine
├── database/             # Data storage
├── examples/             # Example usage
├── models/               # Component models
├── ui/                   # User interfaces
├── utils/                # Utility functions
├── validation/           # Validation framework
├── analytics/            # Usage analytics
├── data/                 # Data files
├── tests/                # Test suite
└── docs/                 # Documentation
```

### Running Tests

```bash
pytest
```

### Building Documentation

```bash
cd docs
sphinx-build -b html . _build
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request


## Contact

For questions or support, please contact:
- Email: cooling-calculator@example.com
- Issue Tracker: https://github.com/your-organization/data-center-cooling-calculator/issues