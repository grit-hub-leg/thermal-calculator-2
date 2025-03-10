# api/app.py

"""
REST API for the Data Center Cooling Calculator.

This module provides a Flask application that exposes the calculator functionality
via RESTful endpoints.
"""

from flask import Flask, request, jsonify, send_file
import os
import json
import logging
from typing import Dict, Any
import tempfile
import threading

# Import calculator
from main import DataCenterCoolingCalculator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create global calculator instance
calculator = DataCenterCoolingCalculator()

def create_api_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure application
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        REPORT_DIR=os.environ.get('REPORT_DIR', os.path.join(tempfile.gettempdir(), 'cooling_reports')),
        DEBUG=os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    )
    
    # Ensure report directory exists
    os.makedirs(app.config['REPORT_DIR'], exist_ok=True)
    
    @app.route('/api/calculate', methods=['POST'])
    def calculate():
        """
        Calculate cooling performance.
        
        Expects a JSON payload with the following required fields:
        - cooling_kw: Required cooling capacity in kW
        - room_temp: Room temperature in °C
        - desired_temp: Desired room temperature in °C
        - water_temp: Water supply temperature in °C
        
        Optional fields are also supported (see calculator documentation).
        
        Returns:
            JSON response with calculation results
        """
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract required parameters
        try:
            cooling_kw = float(data.get('cooling_kw'))
            room_temp = float(data.get('room_temp'))
            desired_temp = float(data.get('desired_temp'))
            water_temp = float(data.get('water_temp'))
        except (TypeError, ValueError):
            return jsonify({'error': 'Missing or invalid required parameters'}), 400
        
        # Extract optional parameters
        kwargs = {k: v for k, v in data.items() 
                 if k not in ['cooling_kw', 'room_temp', 'desired_temp', 'water_temp']}
        
        # Set report directory if generating reports
        if kwargs.get('generate_reports', False):
            kwargs['report_dir'] = app.config['REPORT_DIR']
        
        # Perform calculation
        try:
            result = calculator.calculate(
                cooling_kw, room_temp, desired_temp, water_temp, **kwargs
            )
            
            # Return error if calculation failed
            if 'error' in result:
                return jsonify({'error': result['error']}), 400
                
            return jsonify(result)
            
        except Exception as e:
            logger.exception("Error during calculation")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/recommend', methods=['POST'])
    def recommend():
        """
        Recommend suitable products based on cooling requirements.
        
        Expects a JSON payload with the following required field:
        - cooling_kw: Required cooling capacity in kW
        
        Optional fields:
        - rack_type: Rack type constraint
        - max_results: Maximum number of recommendations to return
        - include_details: Whether to include detailed product information
        
        Returns:
            JSON response with product recommendations
        """
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract required parameter
        try:
            cooling_kw = float(data.get('cooling_kw'))
        except (TypeError, ValueError):
            return jsonify({'error': 'Missing or invalid cooling_kw parameter'}), 400
        
        # Extract optional parameters
        kwargs = {k: v for k, v in data.items() if k != 'cooling_kw'}
        
        # Get recommendations
        try:
            recommendations = calculator.recommend_products(cooling_kw, **kwargs)
            return jsonify({'recommendations': recommendations})
            
        except Exception as e:
            logger.exception("Error during recommendation")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/products', methods=['GET'])
    def get_products():
        """
        Get all available products.
        
        Returns:
            JSON response with product information
        """
        products = calculator.get_all_products()
        return jsonify({'products': products})
    
    @app.route('/api/products/<product_id>', methods=['GET'])
    def get_product(product_id):
        """
        Get detailed information about a specific product.
        
        Args:
            product_id: Product ID
            
        Returns:
            JSON response with product information
        """
        product = calculator.get_product_info(product_id)
        
        if not product:
            return jsonify({'error': f'Product not found: {product_id}'}), 404
            
        return jsonify({'product': product})
    
    @app.route('/api/reports/<path:filename>', methods=['GET'])
    def get_report(filename):
        """
        Get a generated report file.
        
        Args:
            filename: Report filename
            
        Returns:
            PDF file response or error
        """
        report_path = os.path.join(app.config['REPORT_DIR'], filename)
        
        if not os.path.exists(report_path):
            return jsonify({'error': f'Report not found: {filename}'}), 404
            
        return send_file(report_path)
    
    @app.route('/api/validate', methods=['POST'])
    def validate():
        """
        Validate input parameters without performing a full calculation.
        
        Expects a JSON payload with the following required fields:
        - cooling_kw: Required cooling capacity in kW
        - room_temp: Room temperature in °C
        - desired_temp: Desired room temperature in °C
        - water_temp: Water supply temperature in °C
        
        Optional fields are also supported.
        
        Returns:
            JSON response with validation results
        """
        from utils.validation import validate_input_parameters
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract parameters
        try:
            cooling_kw = float(data.get('cooling_kw', 0))
            room_temp = float(data.get('room_temp', 0))
            desired_temp = float(data.get('desired_temp', 0))
            water_temp = float(data.get('water_temp', 0))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid parameter values'}), 400
        
        # Extract other parameters
        kwargs = {k: v for k, v in data.items() 
                 if k not in ['cooling_kw', 'room_temp', 'desired_temp', 'water_temp']}
        
        # Validate parameters
        validation_result = validate_input_parameters(
            cooling_kw, room_temp, desired_temp, water_temp, **kwargs
        )
        
        return jsonify(validation_result)
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed'}), 405
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

# api/openapi.yaml

"""
OpenAPI specification for the Data Center Cooling Calculator API.

This file contains the OpenAPI/Swagger documentation for the API endpoints.
"""

OPENAPI_SPEC = """
openapi: 3.0.0
info:
  title: Data Center Cooling Calculator API
  description: API for calculating cooling performance of data center heat exchangers
  version: 1.0.0
  
servers:
  - url: http://localhost:5000
    description: Development server
  
paths:
  /api/calculate:
    post:
      summary: Calculate cooling performance
      description: Perform cooling calculations based on input parameters
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - cooling_kw
                - room_temp
                - desired_temp
                - water_temp
              properties:
                cooling_kw:
                  type: number
                  description: Required cooling capacity in kW
                room_temp:
                  type: number
                  description: Room temperature in °C
                desired_temp:
                  type: number
                  description: Desired room temperature in °C
                water_temp:
                  type: number
                  description: Water supply temperature in °C
                product_id:
                  type: string
                  description: Specific product ID to use
                rack_type:
                  type: string
                  description: Rack type (e.g., "42U600", "48U800")
                passive_preferred:
                  type: boolean
                  description: Whether to prefer passive cooling
                fluid_type:
                  type: string
                  enum: [water, ethylene_glycol, propylene_glycol]
                  description: Type of cooling fluid
                glycol_percentage:
                  type: number
                  minimum: 0
                  maximum: 60
                  description: Percentage of glycol in mixture
                units:
                  type: string
                  enum: [metric, imperial]
                  description: Preferred units
      responses:
        '200':
          description: Successful calculation
          content:
            application/json:
              schema:
                type: object
                properties:
                  cooling_capacity:
                    type: number
                  product:
                    type: object
                  water_side:
                    type: object
                  air_side:
                    type: object
                  valve_recommendation:
                    type: object
                  efficiency:
                    type: object
                  commercial:
                    type: object
        '400':
          description: Invalid input parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
  
  /api/recommend:
    post:
      summary: Recommend suitable products
      description: Get product recommendations based on cooling requirements
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - cooling_kw
              properties:
                cooling_kw:
                  type: number
                  description: Required cooling capacity in kW
                rack_type:
                  type: string
                  description: Rack type constraint
                max_results:
                  type: integer
                  description: Maximum number of recommendations to return
                include_details:
                  type: boolean
                  description: Whether to include detailed product information
      responses:
        '200':
          description: Successful recommendations
          content:
            application/json:
              schema:
                type: object
                properties:
                  recommendations:
                    type: array
                    items:
                      type: object
        '400':
          description: Invalid input parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
  
  /api/products:
    get:
      summary: Get all available products
      description: Get information about all available cooling products
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  products:
                    type: array
                    items:
                      type: object
  
  /api/products/{product_id}:
    get:
      summary: Get product details
      description: Get detailed information about a specific product
      parameters:
        - name: product_id
          in: path
          required: true
          schema:
            type: string
          description: Product ID
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  product:
                    type: object
        '404':
          description: Product not found
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
  
  /api/validate:
    post:
      summary: Validate input parameters
      description: Validate input parameters without performing a full calculation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                cooling_kw:
                  type: number
                room_temp:
                  type: number
                desired_temp:
                  type: number
                water_temp:
                  type: number
      responses:
        '200':
          description: Validation results
          content:
            application/json:
              schema:
                type: object
                properties:
                  valid:
                    type: boolean
                  message:
                    type: string
                  warnings:
                    type: array
                    items:
                      type: string
        '400':
          description: Invalid input format
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
"""

if __name__ == "__main__":
    app = create_api_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
