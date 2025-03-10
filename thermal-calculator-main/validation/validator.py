# validation/validator.py

import os
import logging
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from core.engine import CalculationEngine
from utils.regional_data import get_regional_settings

logger = logging.getLogger(__name__)

class CalculationValidator:
    """
    Validation framework for testing calculator accuracy against real-world data.
    
    This class provides tools for validating the calculation engine against
    historical data, theoretical models, and real-world test results.
    """
    
    def __init__(self, calculation_engine: CalculationEngine, test_data_path: str):
        """
        Initialize the validation framework.
        
        Args:
            calculation_engine: The calculation engine to validate
            test_data_path: Path to test data directory
        """
        self.engine = calculation_engine
        self.test_data_path = test_data_path
        
    def validate_against_historical(self, history_file: str) -> Dict[str, Any]:
        """
        Validate calculations against historical site data.
        
        Args:
            history_file: Name of historical data file
            
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating against historical data: {history_file}")
        
        # Load historical data
        history_path = os.path.join(self.test_data_path, 'historical', history_file)
        historical_data = self._load_csv_data(history_path)
        
        if historical_data is None:
            return {'error': f"Could not load historical data: {history_file}"}
        
        # Run validation
        results = self._validate_against_dataset(historical_data)
        
        # Generate validation report
        report = self._generate_validation_report(results, "Historical Data Validation")
        
        return report
    
    def validate_against_test_cases(self, test_case_file: str) -> Dict[str, Any]:
        """
        Validate calculations against defined test cases.
        
        Args:
            test_case_file: Name of test case file
            
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating against test cases: {test_case_file}")
        
        # Load test cases
        test_case_path = os.path.join(self.test_data_path, 'test_cases', test_case_file)
        test_cases = self._load_json_data(test_case_path)
        
        if test_cases is None:
            return {'error': f"Could not load test cases: {test_case_file}"}
        
        # Run each test case and collect results
        validation_results = []
        
        for i, test_case in enumerate(test_cases):
            test_id = test_case.get('id', f"Test Case {i+1}")
            inputs = test_case.get('inputs', {})
            expected = test_case.get('expected', {})
            
            # Run calculation
            try:
                result = self.engine.calculate(
                    inputs.get('cooling_kw', 0),
                    inputs.get('room_temp', 0),
                    inputs.get('desired_temp', 0),
                    inputs.get('water_temp', 0),
                    **{k: v for k, v in inputs.items() if k not in ['cooling_kw', 'room_temp', 'desired_temp', 'water_temp']}
                )
                
                # Validate results against expected values
                validation = self._validate_single_result(result, expected)
                validation['test_id'] = test_id
                validation['inputs'] = inputs
                validation_results.append(validation)
                
            except Exception as e:
                logger.error(f"Error in test case {test_id}: {str(e)}")
                validation_results.append({
                    'test_id': test_id,
                    'inputs': inputs,
                    'error': str(e),
                    'success': False
                })
        
        # Generate validation report
        report = self._generate_test_case_report(validation_results, "Test Case Validation")
        
        return report
    
    def validate_against_lab_results(self, lab_file: str) -> Dict[str, Any]:
        """
        Validate calculations against laboratory test results.
        
        Args:
            lab_file: Name of laboratory results file
            
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating against lab results: {lab_file}")
        
        # Load lab data
        lab_path = os.path.join(self.test_data_path, 'lab_results', lab_file)
        lab_data = self._load_csv_data(lab_path)
        
        if lab_data is None:
            return {'error': f"Could not load lab results: {lab_file}"}
        
        # Run validation
        results = self._validate_against_dataset(lab_data)
        
        # Generate validation report
        report = self._generate_validation_report(results, "Laboratory Test Validation")
        
        return report
    
    def comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run a comprehensive validation across all available test data.
        
        Returns:
            Dictionary containing comprehensive validation results
        """
        logger.info("Running comprehensive validation")
        
        validation_results = {
            'historical': {},
            'test_cases': {},
            'lab_results': {}
        }
        
        # Historical data validation
        historical_dir = os.path.join(self.test_data_path, 'historical')
        if os.path.exists(historical_dir):
            for filename in os.listdir(historical_dir):
                if filename.endswith('.csv'):
                    result = self.validate_against_historical(filename)
                    validation_results['historical'][filename] = result
        
        # Test case validation
        test_cases_dir = os.path.join(self.test_data_path, 'test_cases')
        if os.path.exists(test_cases_dir):
            for filename in os.listdir(test_cases_dir):
                if filename.endswith('.json'):
                    result = self.validate_against_test_cases(filename)
                    validation_results['test_cases'][filename] = result
        
        # Lab results validation
        lab_results_dir = os.path.join(self.test_data_path, 'lab_results')
        if os.path.exists(lab_results_dir):
            for filename in os.listdir(lab_results_dir):
                if filename.endswith('.csv'):
                    result = self.validate_against_lab_results(filename)
                    validation_results['lab_results'][filename] = result
        
        # Generate summary
        summary = self._generate_comprehensive_summary(validation_results)
        validation_results['summary'] = summary
        
        return validation_results
    
    def _validate_against_dataset(self, dataset: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Validate calculator against a dataset.
        
        Args:
            dataset: DataFrame containing test data
            
        Returns:
            List of validation results for each row
        """
        validation_results = []
        
        for i, row in dataset.iterrows():
            # Extract input parameters
            try:
                cooling_kw = float(row.get('cooling_kw', 0))
                room_temp = float(row.get('room_temp', 0))
                desired_temp = float(row.get('desired_temp', 0))
                water_temp = float(row.get('water_temp', 0))
                
                # Extract additional parameters
                additional_params = {}
                for col in dataset.columns:
                    if col not in ['cooling_kw', 'room_temp', 'desired_temp', 'water_temp', 
                                 'test_id', 'date', 'location']:
                        if col in row and not pd.isna(row[col]):
                            additional_params[col] = row[col]
                
                # Run calculation
                result = self.engine.calculate(
                    cooling_kw, room_temp, desired_temp, water_temp, **additional_params
                )
                
                # Extract expected values for comparison
                expected = {}
                for col in dataset.columns:
                    if col.startswith('expected_'):
                        param_name = col[9:]  # Remove 'expected_' prefix
                        if not pd.isna(row[col]):
                            expected[param_name] = row[col]
                
                # Validate results against expected values
                validation = self._validate_single_result(result, expected)
                validation['test_id'] = row.get('test_id', f"Row {i+1}")
                validation['inputs'] = {
                    'cooling_kw': cooling_kw,
                    'room_temp': room_temp,
                    'desired_temp': desired_temp,
                    'water_temp': water_temp,
                    **additional_params
                }
                validation_results.append(validation)
                
            except Exception as e:
                logger.error(f"Error in dataset row {i}: {str(e)}")
                validation_results.append({
                    'test_id': row.get('test_id', f"Row {i+1}"),
                    'error': str(e),
                    'success': False
                })
        
        return validation_results
    
    def _validate_single_result(self, result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single calculation result against expected values.
        
        Args:
            result: Dictionary containing calculation results
            expected: Dictionary containing expected values
            
        Returns:
            Dictionary containing validation results
        """
        validation = {
            'success': True,
            'comparisons': []
        }
        
        # Flatten the result dictionary for easier comparison
        flat_result = self._flatten_dict(result)
        
        # Compare each expected value
        for key, expected_value in expected.items():
            if key in flat_result:
                calculated_value = flat_result[key]
                
                # Convert to float for numeric comparison
                try:
                    expected_value = float(expected_value)
                    calculated_value = float(calculated_value)
                    
                    # Calculate deviation
                    absolute_error = abs(calculated_value - expected_value)
                    relative_error = absolute_error / expected_value if expected_value != 0 else float('inf')
                    
                    # Check if within tolerance
                    # Using 5% tolerance by default
                    tolerance = 0.05
                    within_tolerance = relative_error <= tolerance
                    
                    comparison = {
                        'parameter': key,
                        'expected': expected_value,
                        'calculated': calculated_value,
                        'absolute_error': absolute_error,
                        'relative_error': relative_error,
                        'within_tolerance': within_tolerance
                    }
                    
                    validation['comparisons'].append(comparison)
                    
                    # Update overall success
                    if not within_tolerance:
                        validation['success'] = False
                        
                except (ValueError, TypeError):
                    # Non-numeric comparison
                    within_tolerance = expected_value == calculated_value
                    
                    comparison = {
                        'parameter': key,
                        'expected': expected_value,
                        'calculated': calculated_value,
                        'within_tolerance': within_tolerance
                    }
                    
                    validation['comparisons'].append(comparison)
                    
                    # Update overall success
                    if not within_tolerance:
                        validation['success'] = False
            else:
                # Expected parameter not found in results
                validation['comparisons'].append({
                    'parameter': key,
                    'expected': expected_value,
                    'calculated': 'Not found',
                    'within_tolerance': False
                })
                
                validation['success'] = False
        
        return validation
    
    def _generate_validation_report(self, validation_results: List[Dict[str, Any]], 
                                   title: str) -> Dict[str, Any]:
        """
        Generate a validation report from results.
        
        Args:
            validation_results: List of validation results
            title: Report title
            
        Returns:
            Dictionary containing validation report
        """
        # Count successes and failures
        total_tests = len(validation_results)
        successful_tests = sum(1 for result in validation_results if result.get('success', False))
        
        # Calculate overall success rate
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Collect parameter statistics
        parameter_stats = {}
        
        for result in validation_results:
            for comparison in result.get('comparisons', []):
                parameter = comparison.get('parameter')
                
                if parameter not in parameter_stats:
                    parameter_stats[parameter] = {
                        'count': 0,
                        'success_count': 0,
                        'absolute_errors': [],
                        'relative_errors': []
                    }
                
                parameter_stats[parameter]['count'] += 1
                
                if comparison.get('within_tolerance', False):
                    parameter_stats[parameter]['success_count'] += 1
                
                if 'absolute_error' in comparison:
                    parameter_stats[parameter]['absolute_errors'].append(comparison['absolute_error'])
                
                if 'relative_error' in comparison:
                    parameter_stats[parameter]['relative_errors'].append(comparison['relative_error'])
        
        # Calculate parameter statistics
        for param, stats in parameter_stats.items():
            stats['success_rate'] = (stats['success_count'] / stats['count']) * 100 if stats['count'] > 0 else 0
            
            if stats['absolute_errors']:
                stats['mean_absolute_error'] = sum(stats['absolute_errors']) / len(stats['absolute_errors'])
                stats['max_absolute_error'] = max(stats['absolute_errors'])
            
            if stats['relative_errors']:
                stats['mean_relative_error'] = sum(stats['relative_errors']) / len(stats['relative_errors'])
                stats['max_relative_error'] = max(stats['relative_errors'])
        
        # Generate visualization data
        visualization_data = self._generate_visualization_data(validation_results)
        
        # Create report
        report = {
            'title': title,
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate,
            'parameter_stats': parameter_stats,
            'visualization_data': visualization_data,
            'results': validation_results
        }
        
        return report
    
    def _generate_test_case_report(self, validation_results: List[Dict[str, Any]], 
                                  title: str) -> Dict[str, Any]:
        """
        Generate a report for test case validation.
        
        Args:
            validation_results: List of validation results
            title: Report title
            
        Returns:
            Dictionary containing validation report
        """
        # Generate basic report
        report = self._generate_validation_report(validation_results, title)
        
        # Add test case specific information
        test_case_summary = []
        
        for result in validation_results:
            summary = {
                'test_id': result.get('test_id', 'Unknown'),
                'success': result.get('success', False),
                'error': result.get('error', None),
                'parameter_count': len(result.get('comparisons', [])),
                'parameters_within_tolerance': sum(1 for comp in result.get('comparisons', []) 
                                               if comp.get('within_tolerance', False)),
            }
            
            test_case_summary.append(summary)
        
        report['test_case_summary'] = test_case_summary
        
        return report
    
    def _generate_comprehensive_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary for comprehensive validation.
        
        Args:
            validation_results: Dictionary containing all validation results
            
        Returns:
            Dictionary containing summary statistics
        """
        summary = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'overall_success_rate': 0,
            'total_tests': 0,
            'successful_tests': 0,
            'categories': {}
        }
        
        total_tests = 0
        successful_tests = 0
        
        # Process each category
        for category, category_results in validation_results.items():
            if category == 'summary':
                continue
                
            category_summary = {
                'total_tests': 0,
                'successful_tests': 0,
                'success_rate': 0,
                'files': {}
            }
            
            for filename, file_result in category_results.items():
                file_total_tests = file_result.get('total_tests', 0)
                file_successful_tests = file_result.get('successful_tests', 0)
                file_success_rate = file_result.get('success_rate', 0)
                
                category_summary['files'][filename] = {
                    'total_tests': file_total_tests,
                    'successful_tests': file_successful_tests,
                    'success_rate': file_success_rate
                }
                
                category_summary['total_tests'] += file_total_tests
                category_summary['successful_tests'] += file_successful_tests
                
                total_tests += file_total_tests
                successful_tests += file_successful_tests
            
            # Calculate category success rate
            if category_summary['total_tests'] > 0:
                category_summary['success_rate'] = (category_summary['successful_tests'] / 
                                                   category_summary['total_tests']) * 100
            
            summary['categories'][category] = category_summary
        
        # Calculate overall success rate
        if total_tests > 0:
            summary['overall_success_rate'] = (successful_tests / total_tests) * 100
            
        summary['total_tests'] = total_tests
        summary['successful_tests'] = successful_tests
        
        return summary
    
    def _generate_visualization_data(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate data for visualization.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Dictionary containing visualization data
        """
        # Collect parameter errors
        parameter_errors = {}
        
        for result in validation_results:
            for comparison in result.get('comparisons', []):
                parameter = comparison.get('parameter')
                
                if 'relative_error' in comparison:
                    if parameter not in parameter_errors:
                        parameter_errors[parameter] = []
                        
                    parameter_errors[parameter].append({
                        'test_id': result.get('test_id', 'Unknown'),
                        'expected': comparison.get('expected'),
                        'calculated': comparison.get('calculated'),
                        'relative_error': comparison.get('relative_error'),
                        'within_tolerance': comparison.get('within_tolerance')
                    })
        
        # Create scatter plot data
        scatter_data = {}
        
        for parameter, errors in parameter_errors.items():
            # Prepare scatter plot data (expected vs calculated)
            expected_values = [error.get('expected') for error in errors 
                              if error.get('expected') is not None and error.get('calculated') is not None]
            
            calculated_values = [error.get('calculated') for error in errors 
                               if error.get('expected') is not None and error.get('calculated') is not None]
            
            if expected_values and calculated_values:
                # Create linear fit
                coeffs = np.polyfit(expected_values, calculated_values, 1)
                polynomial = np.poly1d(coeffs)
                
                # Generate points for fit line
                x_fit = np.linspace(min(expected_values), max(expected_values), 100)
                y_fit = polynomial(x_fit)
                
                # Calculate R-squared
                y_mean = sum(calculated_values) / len(calculated_values)
                ss_total = sum((y - y_mean) ** 2 for y in calculated_values)
                ss_residual = sum((y - polynomial(x)) ** 2 for x, y in zip(expected_values, calculated_values))
                r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
                
                scatter_data[parameter] = {
                    'expected': expected_values,
                    'calculated': calculated_values,
                    'fit_x': x_fit.tolist(),
                    'fit_y': y_fit.tolist(),
                    'slope': coeffs[0],
                    'intercept': coeffs[1],
                    'r_squared': r_squared
                }
        
        # Create histogram data for relative errors
        histogram_data = {}
        
        for parameter, errors in parameter_errors.items():
            relative_errors = [error.get('relative_error', 0) for error in errors 
                             if error.get('relative_error') is not None]
            
            if relative_errors:
                histogram_data[parameter] = relative_errors
        
        return {
            'scatter': scatter_data,
            'histogram': histogram_data
        }
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten a nested dictionary.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key string
            sep: Separator string
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
                
        return dict(items)
    
    def _load_csv_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Load data from a CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame containing loaded data or None if error
        """
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {str(e)}")
            return None
    
    def _load_json_data(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load data from a JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List containing loaded data or None if error
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            return None
    
    def generate_validation_plots(self, report: Dict[str, Any], output_dir: str) -> List[str]:
        """
        Generate validation plots for a report.
        
        Args:
            report: Validation report dictionary
            output_dir: Directory to save plots
            
        Returns:
            List of generated plot file paths
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        
        # Generate plots only if there's visualization data
        if 'visualization_data' not in report:
            return generated_files
        
        vis_data = report['visualization_data']
        
        # Generate scatter plots
        if 'scatter' in vis_data:
            for parameter, data in vis_data['scatter'].items():
                # Create figure
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Plot data points
                ax.scatter(data['expected'], data['calculated'], alpha=0.7)
                
                # Plot perfect fit line (y=x)
                min_val = min(min(data['expected']), min(data['calculated']))
                max_val = max(max(data['expected']), max(data['calculated']))
                ax.plot([min_val, max_val], [min_val, max_val], 'k--', label='Perfect fit')
                
                # Plot actual fit line
                ax.plot(data['fit_x'], data['fit_y'], 'r-', label=f"Fit: y = {data['slope']:.3f}x + {data['intercept']:.3f} (R² = {data['r_squared']:.3f})")
                
                # Set labels and title
                ax.set_xlabel('Expected Value')
                ax.set_ylabel('Calculated Value')
                ax.set_title(f"Validation Results: {parameter}")
                
                # Add legend
                ax.legend()
                
                # Add grid
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Save figure
                filename = f"scatter_{parameter.replace('.', '_')}.png"
                filepath = os.path.join(output_dir, filename)
                fig.savefig(filepath, dpi=100, bbox_inches='tight')
                plt.close(fig)
                
                generated_files.append(filepath)
        
        # Generate histogram plots
        if 'histogram' in vis_data:
            for parameter, data in vis_data['histogram'].items():
                # Create figure
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Plot histogram
                ax.hist(data, bins=20, alpha=0.7)
                
                # Set labels and title
                ax.set_xlabel('Relative Error')
                ax.set_ylabel('Frequency')
                ax.set_title(f"Error Distribution: {parameter}")
                
                # Add vertical line at tolerance level (5%)
                ax.axvline(x=0.05, color='r', linestyle='--', label='5% Tolerance')
                
                # Add legend
                ax.legend()
                
                # Add grid
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Save figure
                filename = f"histogram_{parameter.replace('.', '_')}.png"
                filepath = os.path.join(output_dir, filename)
                fig.savefig(filepath, dpi=100, bbox_inches='tight')
                plt.close(fig)
                
                generated_files.append(filepath)
        
        # Generate summary plot
        if 'parameter_stats' in report:
            # Extract parameters and success rates
            parameters = list(report['parameter_stats'].keys())
            success_rates = [report['parameter_stats'][param]['success_rate'] for param in parameters]
            
            if parameters:
                # Create figure
                fig, ax = plt.subplots(figsize=(12, 8))
                
                # Sort by success rate
                sorted_indices = np.argsort(success_rates)
                sorted_parameters = [parameters[i] for i in sorted_indices]
                sorted_rates = [success_rates[i] for i in sorted_indices]
                
                # Plot horizontal bar chart
                y_pos = np.arange(len(sorted_parameters))
                ax.barh(y_pos, sorted_rates, align='center')
                ax.set_yticks(y_pos)
                ax.set_yticklabels(sorted_parameters)
                
                # Set labels and title
                ax.set_xlabel('Success Rate (%)')
                ax.set_title('Parameter Validation Success Rates')
                
                # Add vertical line at 95%
                ax.axvline(x=95, color='r', linestyle='--', label='95% Target')
                
                # Add legend
                ax.legend()
                
                # Add grid
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Save figure
                filename = "parameter_success_rates.png"
                filepath = os.path.join(output_dir, filename)
                fig.savefig(filepath, dpi=100, bbox_inches='tight')
                plt.close(fig)
                
                generated_files.append(filepath)
        
        return generated_files

# validation/test_cases.py

import json
import os
from typing import Dict, Any, List, Optional

class TestCaseGenerator:
    """
    Generate test cases for calculator validation.
    
    This class provides tools for generating test cases for the validation framework,
    including edge cases, typical cases, and random cases.
    """
    
    def __init__(self, output_dir: str, product_database: Dict[str, Any], regional_database: Dict[str, Any]):
        """
        Initialize the test case generator.
        
        Args:
            output_dir: Directory to save generated test cases
            product_database: Dictionary of product specifications
            regional_database: Dictionary of regional settings
        """
        self.output_dir = output_dir
        self.products = product_database
        self.regional_data = regional_database
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_standard_test_suite(self, filename: str = "standard_test_cases.json") -> List[Dict[str, Any]]:
        """
        Generate a standard suite of test cases.
        
        Args:
            filename: Name of output file
            
        Returns:
            List of generated test cases
        """
        test_cases = []
        
        # Add typical cases
        test_cases.extend(self._generate_typical_cases())
        
        # Add edge cases
        test_cases.extend(self._generate_edge_cases())
        
        # Add regional cases
        test_cases.extend(self._generate_regional_cases())
        
        # Add fluid type cases
        test_cases.extend(self._generate_fluid_type_cases())
        
        # Save test cases to file
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, 'w') as f:
            json.dump(test_cases, f, indent=2)
        
        return test_cases
    
    def _generate_typical_cases(self) -> List[Dict[str, Any]]:
        """
        Generate typical test cases.
        
        Returns:
            List of typical test cases
        """
        cases = []
        
        # Typical case 1: Medium cooling load
        cases.append({
            'id': 'typical_medium_load',
            'description': 'Typical medium cooling load',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'europe',
                'altitude': 0,
                'fluid_type': 'water',
                'rack_type': '42U800'
            },
            'expected': {
                'water_side.flow_rate': 8.6,  # Placeholder expected values
                'water_side.delta_t': 5.0,
                'air_side.fan_speed_percentage': 75.0,
                'valve_recommendation.sufficient': True
            }
        })
        
        # Typical case 2: Low cooling load
        cases.append({
            'id': 'typical_low_load',
            'description': 'Typical low cooling load',
            'inputs': {
                'cooling_kw': 25,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'europe',
                'altitude': 0,
                'fluid_type': 'water',
                'rack_type': '42U600'
            },
            'expected': {
                'water_side.flow_rate': 4.3,  # Placeholder expected values
                'water_side.delta_t': 5.0,
                'air_side.fan_speed_percentage': 50.0,
                'valve_recommendation.sufficient': True
            }
        })
        
        # Typical case 3: High cooling load
        cases.append({
            'id': 'typical_high_load',
            'description': 'Typical high cooling load',
            'inputs': {
                'cooling_kw': 80,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'europe',
                'altitude': 0,
                'fluid_type': 'water',
                'rack_type': '48U800'
            },
            'expected': {
                'water_side.flow_rate': 13.7,  # Placeholder expected values
                'water_side.delta_t': 5.0,
                'air_side.fan_speed_percentage': 90.0,
                'valve_recommendation.sufficient': True
            }
        })
        
        return cases
    
    def _generate_edge_cases(self) -> List[Dict[str, Any]]:
        """
        Generate edge case test cases.
        
        Returns:
            List of edge case test cases
        """
        cases = []
        
        # Edge case 1: Very high cooling load
        cases.append({
            'id': 'edge_very_high_load',
            'description': 'Very high cooling load, may exceed capacity',
            'inputs': {
                'cooling_kw': 120,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'europe',
                'altitude': 0,
                'fluid_type': 'water',
                'rack_type': '48U800'
            },
            'expected': {
                'water_side.flow_rate': 20.6,  # Placeholder expected values
                'valve_recommendation.sufficient': False,  # Expect valve to be insufficient
                'product_recommended_different': True  # Expect a different product to be recommended
            }
        })
        
        # Edge case 2: Very low temperature difference
        cases.append({
            'id': 'edge_low_temp_diff',
            'description': 'Very low temperature difference between room and desired',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 22.5,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'europe',
                'altitude': 0,
                'fluid_type': 'water',
                'rack_type': '42U800'
            },
            'expected': {
                'air_side.air_flow': 36000,  # Placeholder expected values
                'air_side.fan_speed_percentage': 100.0  # Expect high fan speed due to low temp diff
            }
        })
        
        # Edge case 3: High altitude
        cases.append({
            'id': 'edge_high_altitude',
            'description': 'Installation at high altitude',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'europe',
                'altitude': 2000,  # 2000m altitude
                'fluid_type': 'water',
                'rack_type': '42U800'
            },
            'expected': {
                'air_side.air_flow': 9500,  # Placeholder expected values
                'air_side.fan_speed_percentage': 85.0  # Expect higher fan speed due to thinner air
            }
        })
        
        # Edge case 4: Warm water
        cases.append({
            'id': 'edge_warm_water',
            'description': 'Warm water supply',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 25,  # Warm water, may be difficult to achieve cooling
                'location': 'europe',
                'altitude': 0,
                'fluid_type': 'water',
                'rack_type': '42U800'
            },
            'expected': {
                'warning_generated': True,  # Expect warning due to warm water
                'water_side.flow_rate': 17.2  # Placeholder expected values
            }
        })
        
        return cases
    
    def _generate_regional_cases(self) -> List[Dict[str, Any]]:
        """
        Generate region-specific test cases.
        
        Returns:
            List of region-specific test cases
        """
        cases = []
        
        # North America case
        cases.append({
            'id': 'regional_north_america',
            'description': 'North America installation (208V)',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 75,  # in °F
                'desired_temp': 72,  # in °F
                'water_temp': 60,  # in °F
                'location': 'north_america',
                'altitude': 0,
                'fluid_type': 'water',
                'rack_type': '42U800',
                'voltage': 208,
                'units': 'imperial'
            },
            'expected': {
                'water_side.flow_rate': 8.6,  # Placeholder expected values
                'air_side.power_consumption': 320  # Expect different power due to voltage
            }
        })
        
        # Nordic region case
        cases.append({
            'id': 'regional_nordic',
            'description': 'Nordic region installation with glycol',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'nordic',
                'altitude': 0,
                'fluid_type': 'propylene_glycol',  # As mentioned in transcript for Nordic
                'glycol_percentage': 30,
                'rack_type': '42U800'
            },
            'expected': {
                'water_side.flow_rate': 9.2,  # Placeholder expected values, higher due to glycol
                'water_side.pressure_drop': 15.0  # Expect higher pressure drop due to glycol
            }
        })
        
        # Singapore case
        cases.append({
            'id': 'regional_singapore',
            'description': 'Singapore installation (high ambient temperature)',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 30,  # Higher ambient temp
                'desired_temp': 25,
                'water_temp': 18,  # Minimum water temp for Singapore as mentioned in transcript
                'location': 'singapore',
                'altitude': 0,
                'fluid_type': 'water',
                'rack_type': '42U800'
            },
            'expected': {
                'water_side.flow_rate': 8.6,  # Placeholder expected values
                'dew_point_concerns': True  # Expect dew point warning for Singapore
            }
        })
        
        return cases
    
    def _generate_fluid_type_cases(self) -> List[Dict[str, Any]]:
        """
        Generate test cases for different fluid types.
        
        Returns:
            List of fluid type test cases
        """
        cases = []
        
        # Ethylene glycol case
        cases.append({
            'id': 'fluid_ethylene_glycol',
            'description': 'Ethylene glycol mixture (30%)',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'europe',
                'altitude': 0,
                'fluid_type': 'ethylene_glycol',
                'glycol_percentage': 30,
                'rack_type': '42U800'
            },
            'expected': {
                'water_side.flow_rate': 9.3,  # Placeholder expected values
                'water_side.pressure_drop': 16.0  # Expect higher pressure drop due to glycol
            }
        })
        
        # High glycol percentage case
        cases.append({
            'id': 'fluid_high_glycol',
            'description': 'High glycol percentage (50%)',
            'inputs': {
                'cooling_kw': 50,
                'room_temp': 24,
                'desired_temp': 22,
                'water_temp': 15,
                'location': 'europe',
                'altitude': 0,
                'fluid_type': 'propylene_glycol',
                'glycol_percentage': 50,
                'rack_type': '42U800'
            },
            'expected': {
                'water_side.flow_rate': 10.5,  # Placeholder expected values
                'water_side.pressure_drop': 22.0  # Expect much higher pressure drop
            }
        })
        
        return cases

# validation/historical_data_processor.py

import pandas as pd
import os
import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class HistoricalDataProcessor:
    """
    Process historical data for use in validation.
    
    This class provides tools for processing and normalizing historical data
    from site acceptance tests, making it suitable for validation.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize the historical data processor.
        
        Args:
            output_dir: Directory to save processed data
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def process_site_data(self, input_file: str, output_file: Optional[str] = None) -> pd.DataFrame:
        """
        Process site acceptance test data.
        
        Args:
            input_file: Path to input file
            output_file: Name of output file (optional)
            
        Returns:
            DataFrame containing processed data
        """
        logger.info(f"Processing site data: {input_file}")
        
        # Determine file type from extension
        _, ext = os.path.splitext(input_file)
        
        if ext.lower() == '.csv':
            df = pd.read_csv(input_file)
        elif ext.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(input_file)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        # Process data
        processed_df = self._process_site_data_frame(df)
        
        # Save processed data if output file specified
        if output_file:
            output_path = os.path.join(self.output_dir, output_file)
            processed_df.to_csv(output_path, index=False)
            logger.info(f"Saved processed data to: {output_path}")
        
        return processed_df
    
    def batch_process_site_data(self, input_dir: str, pattern: str = "*.csv") -> Dict[str, pd.DataFrame]:
        """
        Process multiple site data files in a directory.
        
        Args:
            input_dir: Directory containing input files
            pattern: File pattern to match
            
        Returns:
            Dictionary mapping output filenames to processed DataFrames
        """
        logger.info(f"Batch processing site data in: {input_dir}")
        
        processed_data = {}
        
        # Get list of files matching pattern
        import glob
        input_files = glob.glob(os.path.join(input_dir, pattern))
        
        for input_file in input_files:
            # Generate output filename
            filename = os.path.basename(input_file)
            output_file = f"processed_{filename}"
            
            # Process file
            try:
                df = self.process_site_data(input_file, output_file)
                processed_data[output_file] = df
            except Exception as e:
                logger.error(f"Error processing file {input_file}: {str(e)}")
        
        return processed_data
    
    def merge_historical_data(self, input_files: List[str], output_file: str) -> pd.DataFrame:
        """
        Merge multiple processed data files.
        
        Args:
            input_files: List of input file paths
            output_file: Name of output file
            
        Returns:
            DataFrame containing merged data
        """
        logger.info(f"Merging {len(input_files)} historical data files")
        
        # Load and merge data files
        dfs = []
        
        for input_file in input_files:
            try:
                df = pd.read_csv(input_file)
                dfs.append(df)
            except Exception as e:
                logger.error(f"Error loading file {input_file}: {str(e)}")
        
        if not dfs:
            raise ValueError("No valid input files to merge")
        
        # Concatenate DataFrames
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates
        merged_df = merged_df.drop_duplicates()
        
        # Save merged data
        output_path = os.path.join(self.output_dir, output_file)
        merged_df.to_csv(output_path, index=False)
        logger.info(f"Saved merged data to: {output_path}")
        
        return merged_df
    
    def _process_site_data_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process a site data DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Processed DataFrame
        """
        # This would implement logic to normalize and clean the data
        # Specific implementation would depend on the format of the site data
        
        # Simple example implementation
        # 1. Standardize column names
        df = self._standardize_column_names(df)
        
        # 2. Convert units if necessary
        df = self._convert_units(df)
        
        # 3. Handle missing values
        df = self._handle_missing_values(df)
        
        # 4. Add test IDs if missing
        if 'test_id' not in df.columns:
            df['test_id'] = [f"Test_{i+1}" for i in range(len(df))]
        
        return df
    
    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with standardized column names
        """
        # Create a copy of the DataFrame to avoid modifying the original
        df = df.copy()
        
        # Dictionary mapping possible input column names to standardized names
        name_mapping = {
            # Input parameters
            r'cooling(?:\s*capacity)?(?:\s*\(kw\))?': 'cooling_kw',
            r'(?:room|inlet|ambient)(?:\s*temp(?:erature)?)?(?:\s*\((?:c|°c)\))?': 'room_temp',
            r'(?:desired|target|output)(?:\s*temp(?:erature)?)?(?:\s*\((?:c|°c)\))?': 'desired_temp',
            r'(?:water|supply|fluid)(?:\s*temp(?:erature)?)?(?:\s*\((?:c|°c)\))?': 'water_temp',
            r'(?:altitude|elevation)(?:\s*\(m\))?': 'altitude',
            r'(?:fluid|coolant)(?:\s*type)?': 'fluid_type',
            r'glycol(?:\s*percentage)?(?:\s*\(%\))?': 'glycol_percentage',
            r'(?:rack|cabinet)(?:\s*type)?': 'rack_type',
            
            # Expected output values
            r'(?:measured|actual)(?:\s*flow(?:\s*rate)?)?(?:\s*\(m3/h\))?': 'expected_water_side.flow_rate',
            r'(?:measured|actual)(?:\s*return(?:\s*temp(?:erature)?)?)?(?:\s*\((?:c|°c)\))?': 'expected_water_side.return_temp',
            r'(?:measured|actual)(?:\s*pressure(?:\s*drop)?)?(?:\s*\(kpa\))?': 'expected_water_side.pressure_drop',
            r'(?:measured|actual)(?:\s*fan(?:\s*speed)?)?(?:\s*\(%\))?': 'expected_air_side.fan_speed_percentage',
            r'(?:measured|actual)(?:\s*power(?:\s*consumption)?)?(?:\s*\(w\))?': 'expected_air_side.power_consumption',
            r'(?:measured|actual)(?:\s*noise(?:\s*level)?)?(?:\s*\(db\))?': 'expected_air_side.noise_level'
        }
        
        # Apply mappings to column names
        new_columns = []
        
        for col in df.columns:
            # Convert to lowercase for matching
            col_lower = col.lower()
            
            # Check each pattern
            matched = False
            for pattern, new_name in name_mapping.items():
                if re.search(pattern, col_lower):
                    new_columns.append(new_name)
                    matched = True
                    break
            
            # If no match, keep the original column name
            if not matched:
                new_columns.append(col)
        
        # Rename columns
        df.columns = new_columns
        
        return df
    
    def _convert_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert units to standard units.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with standardized units
        """
        # Create a copy of the DataFrame to avoid modifying the original
        df = df.copy()
        
        # Temperature conversion (°F to °C)
        for col in ['room_temp', 'desired_temp', 'water_temp', 'expected_water_side.return_temp']:
            if col in df.columns:
                # Check if values are likely in Fahrenheit
                if df[col].mean() > 40:  # Heuristic: if mean temperature > 40, likely Fahrenheit
                    df[col] = (df[col] - 32) * 5/9
        
        # Cooling capacity conversion (tons to kW)
        if 'cooling_kw' in df.columns:
            # Check if values are likely in tons
            if df['cooling_kw'].mean() < 10:  # Heuristic: if mean cooling < 10, likely tons
                df['cooling_kw'] = df['cooling_kw'] * 3.517
        
        # Altitude conversion (feet to meters)
        if 'altitude' in df.columns:
            # Check if values are likely in feet
            if df['altitude'].mean() > 1000:  # Heuristic: if mean altitude > 1000, likely feet
                df['altitude'] = df['altitude'] * 0.3048
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in the DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with handled missing values
        """
        # Create a copy of the DataFrame to avoid modifying the original
        df = df.copy()
        
        # For required inputs, drop rows with missing values
        required_columns = ['cooling_kw', 'room_temp', 'desired_temp', 'water_temp']
        df = df.dropna(subset=[col for col in required_columns if col in df.columns])
        
        # For optional parameters, fill with default values
        optional_defaults = {
            'altitude': 0,
            'fluid_type': 'water',
            'glycol_percentage': 0,
            'rack_type': '',
            'pipe_configuration': 'bottom_fed',
            'voltage': 230
        }
        
        for col, default in optional_defaults.items():
            if col in df.columns:
                df[col] = df[col].fillna(default)
        
        return df
