"""
Functions for integrating with Solid Edge CAD software.
"""

import os
import sys
import json
import win32com.client
import pythoncom
from src.thermal_calculator import ThermalCalculator


class SolidEdgeBridge:
    """Bridge between Thermal Calculator and Solid Edge."""
    
    def __init__(self):
        """Initialize the Solid Edge bridge."""
        self.calculator = ThermalCalculator()
        self.solid_edge = None
    
    def connect_to_solid_edge(self):
        """
        Connect to an existing Solid Edge instance or create a new one.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Initialize COM
            pythoncom.CoInitialize()
            
            # Try to connect to a running instance
            try:
                self.solid_edge = win32com.client.GetActiveObject("SolidEdge.Application")
                print("Connected to running Solid Edge instance")
            except:
                # Create a new instance if none is running
                self.solid_edge = win32com.client.Dispatch("SolidEdge.Application")
                self.solid_edge.Visible = True
                print("Started new Solid Edge instance")
            
            return True
        except Exception as e:
            print(f"Error connecting to Solid Edge: {e}")
            return False
    
    def get_material_properties(self, part_document):
        """
        Extract material properties from a Solid Edge part document.
        
        Args:
            part_document: Solid Edge part document object
            
        Returns:
            dict: Material properties
        """
        properties = {}
        
        try:
            # Get the active material
            material_manager = part_document.MaterialManager
            active_material = material_manager.ActiveMaterial
            
            if active_material:
                properties['name'] = active_material.Name
                
                # Get thermal conductivity if available
                try:
                    thermal_props = active_material.GetThermalProperties()
                    properties['thermal_conductivity'] = thermal_props.ThermalConductivity
                except:
                    # Use default values if not available
                    material_name = active_material.Name.lower()
                    for known_material in self.calculator.MATERIAL_CONDUCTIVITY:
                        if known_material in material_name:
                            properties['thermal_conductivity'] = self.calculator.MATERIAL_CONDUCTIVITY[known_material]
                            break
            
            # Get part dimensions
            body = part_document.Models.Item(1)
            range_box = body.RangeBox
            
            # Calculate approximate thickness (simplistic approach)
            properties['thickness'] = min(
                abs(range_box.MaxPoint.X - range_box.MinPoint.X),
                abs(range_box.MaxPoint.Y - range_box.MinPoint.Y),
                abs(range_box.MaxPoint.Z - range_box.MinPoint.Z)
            )
            
        except Exception as e:
            print(f"Error getting material properties: {e}")
        
        return properties
    
    def calculate_from_solid_edge(self, temp_diff=50):
        """
        Calculate thermal properties based on the active Solid Edge part.
        
        Args:
            temp_diff (float): Temperature difference to use in calculations
            
        Returns:
            dict: Calculation results
        """
        results = {}
        
        if not self.solid_edge:
            if not self.connect_to_solid_edge():
                return {"error": "Could not connect to Solid Edge"}
        
        try:
            # Get the active document
            active_doc = self.solid_edge.ActiveDocument
            
            if not active_doc:
                return {"error": "No active document in Solid Edge"}
            
            # Check if it's a part document
            if active_doc.Type != 1:  # 1 = Part document
                return {"error": "Active document is not a part document"}
            
            # Get material properties
            properties = self.get_material_properties(active_doc)
            
            if 'thermal_conductivity' in properties and 'thickness' in properties:
                # Calculate heat transfer
                heat_transfer = self.calculator.calculate_heat_transfer(
                    "custom",  # Using custom material with known conductivity
                    properties['thickness'],
                    temp_diff
                )
                
                results = {
                    "material": properties.get('name', 'Unknown'),
                    "thermal_conductivity": properties.get('thermal_conductivity', 0),
                    "thickness": properties['thickness'],
                    "temperature_difference": temp_diff,
                    "heat_transfer_rate": heat_transfer
                }
            else:
                results = {"error": "Could not determine material properties"}
            
        except Exception as e:
            results = {"error": f"Error in Solid Edge calculation: {e}"}
        
        return results
    
    def export_results_to_solid_edge(self, results, filename=None):
        """
        Export calculation results to Solid Edge as properties.
        
        Args:
            results (dict): Calculation results
            filename (str, optional): Filename to save the part with results
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.solid_edge:
            if not self.connect_to_solid_edge():
                return False
        
        try:
            # Get the active document
            active_doc = self.solid_edge.ActiveDocument
            
            if not active_doc:
                return False
            
            # Add custom properties to the document
            props = active_doc.Properties
            
            # Add or update thermal properties
            for key, value in results.items():
                # Check if property exists
                prop_exists = False
                for i in range(props.Count):
                    if props.Item(i).Name == f"Thermal_{key}":
                        props.Item(i).Value = str(value)
                        prop_exists = True
                        break
                
                # Create new property if it doesn't exist
                if not prop_exists:
                    props.Add(f"Thermal_{key}", str(value))
            
            # Save the document if filename is provided
            if filename:
                active_doc.SaveAs(filename)
            
            return True
            
        except Exception as e:
            print(f"Error exporting results to Solid Edge: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    bridge = SolidEdgeBridge()
    
    if bridge.connect_to_solid_edge():
        results = bridge.calculate_from_solid_edge(temp_diff=75)
        print("Calculation results:", results)
        
        if "error" not in results:
            bridge.export_results_to_solid_edge(results)
            print("Results exported to Solid Edge document properties")

