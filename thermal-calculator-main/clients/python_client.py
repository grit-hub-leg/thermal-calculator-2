# clients/python_client.py

"""
Python client for the Data Center Cooling Calculator API.

This module provides a Python client to interact with the cooling calculator API.
"""

import requests
import json
from typing import Dict, Any, List, Optional, Union

class CoolingCalculatorClient:
    """
    Client for the Data Center Cooling Calculator API.
    
    This class provides methods to interact with the cooling calculator API endpoints.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
    
    def calculate(self, cooling_kw: float, room_temp: float, desired_temp: float, 
                 water_temp: float, **kwargs) -> Dict[str, Any]:
        """
        Calculate cooling performance.
        
        Args:
            cooling_kw: Required cooling capacity in kW
            room_temp: Room temperature in °C
            desired_temp: Desired room temperature in °C
            water_temp: Water supply temperature in °C
            **kwargs: Additional optional parameters
                
        Returns:
            Dictionary containing calculation results
        
        Raises:
            ValueError: If the API returns an error
            requests.RequestException: If the request fails
        """
        # Prepare request data
        data = {
            'cooling_kw': cooling_kw,
            'room_temp': room_temp,
            'desired_temp': desired_temp,
            'water_temp': water_temp,
            **kwargs
        }
        
        # Make API request
        try:
            response = requests.post(f"{self.base_url}/api/calculate", json=data)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            
            if 'error' in result:
                raise ValueError(result['error'])
                
            return result
            
        except requests.RequestException as e:
            raise e
    
    def recommend_products(self, cooling_kw: float, **kwargs) -> List[Dict[str, Any]]:
        """
        Recommend suitable products.
        
        Args:
            cooling_kw: Required cooling capacity in kW
            **kwargs: Additional optional parameters
                
        Returns:
            List of recommended products
        
        Raises:
            ValueError: If the API returns an error
            requests.RequestException: If the request fails
        """
        # Prepare request data
        data = {
            'cooling_kw': cooling_kw,
            **kwargs
        }
        
        # Make API request
        try:
            response = requests.post(f"{self.base_url}/api/recommend", json=data)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            
            if 'error' in result:
                raise ValueError(result['error'])
                
            return result.get('recommendations', [])
            
        except requests.RequestException as e:
            raise e
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Get all available products.
        
        Returns:
            List of all products
        
        Raises:
            ValueError: If the API returns an error
            requests.RequestException: If the request fails
        """
        try:
            response = requests.get(f"{self.base_url}/api/products")
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            
            if 'error' in result:
                raise ValueError(result['error'])
                
            return result.get('products', [])
            
        except requests.RequestException as e:
            raise e
    
    def get_product_info(self, product_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Dictionary containing product information
        
        Raises:
            ValueError: If the API returns an error
            requests.RequestException: If the request fails
        """
        try:
            response = requests.get(f"{self.base_url}/api/products/{product_id}")
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            
            if 'error' in result:
                raise ValueError(result['error'])
                
            return result.get('product', {})
            
        except requests.RequestException as e:
            raise e
    
    def validate_parameters(self, cooling_kw: float, room_temp: float, 
                           desired_temp: float, water_temp: float, 
                           **kwargs) -> Dict[str, Any]:
        """
        Validate input parameters.
        
        Args:
            cooling_kw: Required cooling capacity in kW
            room_temp: Room temperature in °C
            desired_temp: Desired room temperature in °C
            water_temp: Water supply temperature in °C
            **kwargs: Additional optional parameters
                
        Returns:
            Dictionary containing validation results
        
        Raises:
            ValueError: If the API returns an error
            requests.RequestException: If the request fails
        """
        # Prepare request data
        data = {
            'cooling_kw': cooling_kw,
            'room_temp': room_temp,
            'desired_temp': desired_temp,
            'water_temp': water_temp,
            **kwargs
        }
        
        # Make API request
        try:
            response = requests.post(f"{self.base_url}/api/validate", json=data)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            
            if 'error' in result:
                raise ValueError(result['error'])
                
            return result
            
        except requests.RequestException as e:
            raise e
    
    def download_report(self, report_path: str, output_path: str) -> bool:
        """
        Download a generated report.
        
        Args:
            report_path: Path to the report on the server
            output_path: Local path to save the report
            
        Returns:
            True if download was successful, False otherwise
        
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.get(f"{self.base_url}/api/reports/{report_path}", stream=True)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return True
            
        except requests.RequestException as e:
            raise e


# Example usage
if __name__ == "__main__":
    # Create client
    client = CoolingCalculatorClient()
    
    try:
        # Get all products
        products = client.get_all_products()
        print(f"Available products: {len(products)}")
        
        # Get recommendations
        recommendations = client.recommend_products(50)
        print("Recommended products:")
        for product in recommendations:
            print(f"- {product['name']} ({product['id']}): {product['max_cooling_capacity']} kW")
        
        # Perform calculation
        result = client.calculate(
            cooling_kw=50,
            room_temp=24,
            desired_temp=22,
            water_temp=15,
            rack_type="42U800",
            units="metric"
        )
        
        print("\nCalculation Results:")
        print(f"Cooling Capacity: {result['cooling_capacity']} kW")
        print(f"Product: {result['product']['name']}")
        print(f"Water Flow Rate: {result['water_side']['flow_rate']:.2f} m³/h")
        print(f"Fan Speed: {result['air_side']['fan_speed_percentage']:.1f}%")
        print(f"COP: {result['efficiency']['cop']:.2f}")
        
        if 'commercial' in result:
            commercial = result['commercial']
            print(f"Annual Energy Cost: ${commercial['energy_costs']['annual_cost']:.2f}")
            print(f"Payback Period: {commercial['payback_years']:.1f} years")
        
    except Exception as e:
        print(f"Error: {str(e)}")

# clients/javascript_client.js

/**
 * JavaScript client for the Data Center Cooling Calculator API.
 * 
 * This module provides a JavaScript client to interact with the cooling calculator API.
 */

class CoolingCalculatorClient {
    /**
     * Initialize the client.
     * 
     * @param {string} baseUrl - Base URL of the API server
     */
    constructor(baseUrl = 'http://localhost:5000') {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }
    
    /**
     * Calculate cooling performance.
     * 
     * @param {number} coolingKw - Required cooling capacity in kW
     * @param {number} roomTemp - Room temperature in °C
     * @param {number} desiredTemp - Desired room temperature in °C
     * @param {number} waterTemp - Water supply temperature in °C
     * @param {Object} options - Additional optional parameters
     * @returns {Promise<Object>} - Calculation results
     */
    async calculate(coolingKw, roomTemp, desiredTemp, waterTemp, options = {}) {
        // Prepare request data
        const data = {
            cooling_kw: coolingKw,
            room_temp: roomTemp,
            desired_temp: desiredTemp,
            water_temp: waterTemp,
            ...options
        };
        
        // Make API request
        try {
            const response = await fetch(`${this.baseUrl}/api/calculate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            return result;
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * Recommend suitable products.
     * 
     * @param {number} coolingKw - Required cooling capacity in kW
     * @param {Object} options - Additional optional parameters
     * @returns {Promise<Array>} - List of recommended products
     */
    async recommendProducts(coolingKw, options = {}) {
        // Prepare request data
        const data = {
            cooling_kw: coolingKw,
            ...options
        };
        
        // Make API request
        try {
            const response = await fetch(`${this.baseUrl}/api/recommend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            return result.recommendations || [];
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * Get all available products.
     * 
     * @returns {Promise<Array>} - List of all products
     */
    async getAllProducts() {
        try {
            const response = await fetch(`${this.baseUrl}/api/products`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            return result.products || [];
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * Get detailed information about a specific product.
     * 
     * @param {string} productId - Product ID
     * @returns {Promise<Object>} - Product information
     */
    async getProductInfo(productId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/products/${productId}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            return result.product || {};
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * Validate input parameters.
     * 
     * @param {number} coolingKw - Required cooling capacity in kW
     * @param {number} roomTemp - Room temperature in °C
     * @param {number} desiredTemp - Desired room temperature in °C
     * @param {number} waterTemp - Water supply temperature in °C
     * @param {Object} options - Additional optional parameters
     * @returns {Promise<Object>} - Validation results
     */
    async validateParameters(coolingKw, roomTemp, desiredTemp, waterTemp, options = {}) {
        // Prepare request data
        const data = {
            cooling_kw: coolingKw,
            room_temp: roomTemp,
            desired_temp: desiredTemp,
            water_temp: waterTemp,
            ...options
        };
        
        // Make API request
        try {
            const response = await fetch(`${this.baseUrl}/api/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            return result;
        } catch (error) {
            throw error;
        }
    }
}

// Example usage (in browser or Node.js)
async function exampleUsage() {
    // Create client
    const client = new CoolingCalculatorClient();
    
    try {
        // Get all products
        const products = await client.getAllProducts();
        console.log(`Available products: ${products.length}`);
        
        // Get recommendations
        const recommendations = await client.recommendProducts(50);
        console.log("Recommended products:");
        recommendations.forEach(product => {
            console.log(`- ${product.name} (${product.id}): ${product.max_cooling_capacity} kW`);
        });
        
        // Perform calculation
        const result = await client.calculate(
            50,    // cooling_kw
            24,     // room_temp
            22,     // desired_temp
            15,     // water_temp
            {
                rack_type: "42U800",
                units: "metric"
            }
        );
        
        console.log("\nCalculation Results:");
        console.log(`Cooling Capacity: ${result.cooling_capacity} kW`);
        console.log(`Product: ${result.product.name}`);
        console.log(`Water Flow Rate: ${result.water_side.flow_rate.toFixed(2)} m³/h`);
        console.log(`Fan Speed: ${result.air_side.fan_speed_percentage.toFixed(1)}%`);
        console.log(`COP: ${result.efficiency.cop.toFixed(2)}`);
        
        if (result.commercial) {
            const commercial = result.commercial;
            console.log(`Annual Energy Cost: $${commercial.energy_costs.annual_cost.toFixed(2)}`);
            console.log(`Payback Period: ${commercial.payback_years.toFixed(1)} years`);
        }
        
    } catch (error) {
        console.error(`Error: ${error.message}`);
    }
}

// If running in Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CoolingCalculatorClient;
}

# examples/example_usage.py

"""
Example usage of the Data Center Cooling Calculator.

This script demonstrates direct usage of the calculator library.
"""

import sys
import os
import json

# Add parent directory to path to import calculator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import DataCenterCoolingCalculator

def run_examples():
    """Run example calculations to demonstrate calculator usage."""
    # Create calculator instance
    calculator = DataCenterCoolingCalculator()
    
    print("Data Center Cooling Calculator - Example Usage\n")
    
    # Example 1: Basic calculation
    print("Example 1: Basic Calculation")
    print("--------------------------")
    
    result1 = calculator.calculate(
        cooling_kw=50,
        room_temp=24,
        desired_temp=22,
        water_temp=15
    )
    
    print_result_summary(result1)
    
    # Example 2: Active cooling with custom rack type
    print("\nExample 2: Active Cooling with Custom Rack Type")
    print("--------------------------------------------")
    
    result2 = calculator.calculate(
        cooling_kw=60,
        room_temp=25,
        desired_temp=22,
        water_temp=15,
        rack_type="48U800",
        fluid_type="water",
        include_commercial=True
    )
    
    print_result_summary(result2)
    
    # Example 3: Passive cooling
    print("\nExample 3: Passive Cooling")
    print("------------------------")
    
    result3 = calculator.calculate(
        cooling_kw=25,
        room_temp=24,
        desired_temp=22,
        water_temp=14,
        passive_preferred=True,
        server_air_flow=5000,
        server_pressure=25
    )
    
    print_result_summary(result3)
    
    # Example 4: High-performance cooling (HPC)
    print("\nExample 4: High-Performance Cooling")
    print("----------------------------------")
    
    result4 = calculator.calculate(
        cooling_kw=120,
        room_temp=28,
        desired_temp=24,
        water_temp=18,
        product_id="CL23_48U800"  # Directly specify HPC product
    )
    
    print_result_summary(result4)
    
    # Example 5: Product recommendations
    print("\nExample 5: Product Recommendations")
    print("--------------------------------")
    
    recommendations = calculator.recommend_products(
        cooling_kw=80,
        include_details=False
    )
    
    print("Recommended products for 80 kW cooling:")
    for i, product in enumerate(recommendations):
        print(f"{i+1}. {product['name']} ({product['series']})")
        print(f"   - Rack Type: {product['rack_type']}")
        print(f"   - Max Capacity: {product['max_cooling_capacity']} kW")
        print(f"   - Passive: {'Yes' if product.get('passive', False) else 'No'}")
    
    # Example 6: Glycol cooling
    print("\nExample 6: Glycol Cooling")
    print("-----------------------")
    
    result6 = calculator.calculate(
        cooling_kw=50,
        room_temp=24,
        desired_temp=22,
        water_temp=12,
        fluid_type="propylene_glycol",
        glycol_percentage=30,
        location="nordic"  # Nordic region typically uses glycol
    )
    
    print_result_summary(result6)
    
    # Example 7: Imperial units
    print("\nExample 7: Imperial Units")
    print("----------------------")
    
    result7 = calculator.calculate(
        cooling_kw=14,  # 14 tons
        room_temp=75,   # 75°F
        desired_temp=72, # 72°F
        water_temp=60,   # 60°F
        units="imperial"
    )
    
    print_result_summary(result7)

def print_result_summary(result):
    """Print a summary of calculation results."""
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
    
    product = result.get('product', {})
    water_side = result.get('water_side', {})
    air_side = result.get('air_side', {})
    efficiency = result.get('efficiency', {})
    
    print(f"Product: {product.get('name', 'N/A')}")
    print(f"Cooling Capacity: {result.get('cooling_capacity', 0)} kW")
    print(f"Water Flow Rate: {water_side.get('flow_rate', 0):.2f} m³/h")
    print(f"Water Temperatures: {water_side.get('supply_temp', 0):.1f}°C in, {water_side.get('return_temp', 0):.1f}°C out")
    
    if 'fan_speed_percentage' in air_side:
        # Active cooling
        print(f"Fan Speed: {air_side.get('fan_speed_percentage', 0):.1f}%")
        print(f"Power Consumption: {air_side.get('power_consumption', 0):.1f} W")
    else:
        # Passive cooling
        print("Cooling Type: Passive (0 W)")
    
    print(f"Efficiency (COP): {efficiency.get('cop', 0):.2f}")
    
    if 'commercial' in result:
        commercial = result['commercial']
        energy_costs = commercial.get('energy_costs', {})
        environmental = commercial.get('environmental', {})
        
        print(f"Annual Energy Cost: ${energy_costs.get('annual_cost', 0):.2f}")
        print(f"Annual Carbon Emissions: {environmental.get('annual_carbon_kg', 0):.0f} kg CO₂")
        print(f"Payback Period: {commercial.get('payback_years', 0):.1f} years")

if __name__ == "__main__":
    run_examples()
