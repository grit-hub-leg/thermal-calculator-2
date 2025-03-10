"""
Report generation utilities for the Data Center Cooling Calculator.
"""

import os
import json
from datetime import datetime


def generate_report(result, format="json", output_dir=None):
    """
    Generate a report from calculation results
    
    Args:
        result (dict): Calculation result
        format (str): Report format ('json', 'text', 'html')
        output_dir (str, optional): Directory to save report file
        
    Returns:
        str: Report content or file path
    """
    if format == "json":
        return generate_json_report(result, output_dir)
    elif format == "text":
        return generate_text_report(result, output_dir)
    elif format == "html":
        return generate_html_report(result, output_dir)
    else:
        raise ValueError(f"Unsupported report format: {format}")


def generate_json_report(result, output_dir=None):
    """
    Generate a JSON report
    
    Args:
        result (dict): Calculation result
        output_dir (str, optional): Directory to save report file
        
    Returns:
        str: JSON string or file path
    """
    # Add report metadata
    report = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "version": "0.1.0"
        },
        "result": result
    }
    
    # Convert to JSON string
    json_report = json.dumps(report, indent=2)
    
    # Save to file if output directory is provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cooling_report_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(json_report)
        
        return filepath
    
    return json_report


def generate_text_report(result, output_dir=None):
    """
    Generate a plain text report
    
    Args:
        result (dict): Calculation result
        output_dir (str, optional): Directory to save report file
        
    Returns:
        str: Text report or file path
    """
    # Initialize lines for the report
    lines = []
    
    # Add header
    lines.append("="*80)
    lines.append("                 DATA CENTER COOLING CALCULATION REPORT")
    lines.append(f"                      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("="*80)
    lines.append("")
    
    # Add input parameters
    lines.append("-"*80)
    lines.append("INPUT PARAMETERS")
    lines.append("-"*80)
    
    if "input_parameters" in result:
        params = result["input_parameters"]
        lines.append(f"Cooling Capacity:     {params.get('cooling_kw', 'N/A'):.1f} kW")
        lines.append(f"Room Temperature:     {params.get('room_temp', 'N/A'):.1f} °C")
        lines.append(f"Desired Temperature:  {params.get('desired_temp', 'N/A'):.1f} °C")
        lines.append(f"Water Temperature:    {params.get('water_temp', 'N/A'):.1f} °C")
        lines.append(f"Fluid Type:           {params.get('fluid_type', 'water')}")
        lines.append(f"Glycol Percentage:    {params.get('glycol_percentage', 0)}%")
    lines.append("")
    
    # Add product information
    lines.append("-"*80)
    lines.append("RECOMMENDED PRODUCT")
    lines.append("-"*80)
    
    if "product" in result and result["product"]:
        product = result["product"]
        lines.append(f"Product:               {product.get('name', 'N/A')}")
        lines.append(f"Series:                {product.get('series', 'N/A')}")
        lines.append(f"Description:           {product.get('description', 'N/A')}")
        lines.append(f"Max Cooling Capacity:  {product.get('max_cooling_capacity', 'N/A'):.1f} kW")
    else:
        lines.append("No product recommendation available.")
    lines.append("")
    
    # Add water side results
    lines.append("-"*80)
    lines.append("WATER SIDE RESULTS")
    lines.append("-"*80)
    
    if "water_side" in result:
        water = result["water_side"]
        lines.append(f"Flow Rate:             {water.get('flow_rate', 'N/A'):.2f} m³/h")
        lines.append(f"Pressure Drop:         {water.get('pressure_drop', 'N/A'):.1f} kPa")
        lines.append(f"Pump Power:            {water.get('pump_power', 'N/A'):.3f} kW")
        if "temperature_in" in water and "temperature_out" in water:
            lines.append(f"Water Inlet Temp:      {water.get('temperature_in', 'N/A'):.1f} °C")
            lines.append(f"Water Outlet Temp:     {water.get('temperature_out', 'N/A'):.1f} °C")
            lines.append(f"Water Delta-T:         {water.get('delta_t', 'N/A'):.1f} °C")
    lines.append("")
    
    # Add air side results
    lines.append("-"*80)
    lines.append("AIR SIDE RESULTS")
    lines.append("-"*80)
    
    if "air_side" in result:
        air = result["air_side"]
        lines.append(f"Air Flow Rate:         {air.get('flow_rate', 'N/A'):.1f} m³/h")
        lines.append(f"Fan Speed:             {air.get('fan_speed_percentage', 'N/A'):.1f}%")
        lines.append(f"Fan Power:             {air.get('fan_power', 'N/A'):.3f} kW")
        if "temperature_in" in air and "temperature_out" in air:
            lines.append(f"Air Inlet Temp:        {air.get('temperature_in', 'N/A'):.1f} °C")
            lines.append(f"Air Outlet Temp:       {air.get('temperature_out', 'N/A'):.1f} °C")
            lines.append(f"Air Delta-T:           {air.get('delta_t', 'N/A'):.1f} °C")
    lines.append("")
    
    # Add heat transfer results
    if "heat_transfer" in result:
        lines.append("-"*80)
        lines.append("HEAT TRANSFER RESULTS")
        lines.append("-"*80)
        
        heat = result["heat_transfer"]
        lines.append(f"Cooling Capacity:      {heat.get('cooling_capacity', 'N/A'):.1f} kW")
        lines.append(f"Effectiveness:         {heat.get('effectiveness', 'N/A'):.3f}")
        lines.append(f"LMTD:                  {heat.get('lmtd', 'N/A'):.1f} °C")
        lines.append(f"UA Value:              {heat.get('ua_value', 'N/A'):.1f} kW/K")
        lines.append("")
    
    # Add efficiency results
    if "efficiency" in result:
        lines.append("-"*80)
        lines.append("EFFICIENCY RESULTS")
        lines.append("-"*80)
        
        eff = result["efficiency"]
        lines.append(f"COP:                   {eff.get('cop', 'N/A'):.1f}")
        lines.append(f"EER:                   {eff.get('eer', 'N/A'):.1f}")
        lines.append(f"Total Power:           {eff.get('total_power', 'N/A'):.3f} kW")
        lines.append("")
    
    # Add commercial results if available
    if "commercial" in result:
        lines.append("-"*80)
        lines.append("COMMERCIAL ANALYSIS")
        lines.append("-"*80)
        
        comm = result["commercial"]
        
        if "capital_costs" in comm:
            cap = comm["capital_costs"]
            lines.append(f"Product Cost:          ${cap.get('product', 'N/A'):,.2f}")
            lines.append(f"Installation Cost:     ${cap.get('installation', 'N/A'):,.2f}")
            lines.append(f"Total Capital Cost:    ${cap.get('total', 'N/A'):,.2f}")
            lines.append("")
        
        if "operational_costs" in comm:
            op = comm["operational_costs"]
            lines.append(f"Annual Electricity:    ${op.get('annual_electricity', 'N/A'):,.2f}")
            lines.append(f"Annual Maintenance:    ${op.get('annual_maintenance', 'N/A'):,.2f}")
            lines.append(f"Annual Total Cost:     ${op.get('annual_total', 'N/A'):,.2f}")
            lines.append(f"Annual Savings:        ${op.get('annual_savings', 'N/A'):,.2f}")
            lines.append("")
        
        if "roi" in comm:
            roi = comm["roi"]
            lines.append(f"Payback Period:        {roi.get('simple_payback_years', 'N/A'):.1f} years")
            lines.append(f"Annual ROI:            {roi.get('annual_roi_percentage', 'N/A'):.1f}%")
            lines.append("")
        
        if "tco" in comm:
            tco = comm["tco"]
            lines.append(f"10-Year TCO:           ${tco.get('total', 'N/A'):,.2f}")
            lines.append(f"Traditional TCO:       ${tco.get('traditional_total', 'N/A'):,.2f}")
            lines.append(f"TCO Savings:           ${tco.get('savings', 'N/A'):,.2f}")
            lines.append("")
        
        if "environmental" in comm:
            env = comm["environmental"]
            lines.append(f"Annual Energy Savings: {env.get('annual_energy_savings_kwh', 'N/A'):,.1f} kWh")
            lines.append(f"Annual CO2 Reduction:  {env.get('annual_carbon_reduction_kg', 'N/A'):,.1f} kg")
            lines.append(f"Lifetime CO2 Reduction:{env.get('lifetime_carbon_reduction_kg', 'N/A'):,.1f} kg")
            lines.append("")
    
    # Add warnings
    if "warnings" in result and result["warnings"]:
        lines.append("-"*80)
        lines.append("WARNINGS")
        lines.append("-"*80)
        
        for i, warning in enumerate(result["warnings"], 1):
            lines.append(f"{i}. {warning}")
        lines.append("")
    
    # Add footer
    lines.append("="*80)
    lines.append("                          END OF REPORT")
    lines.append("="*80)
    
    # Join all lines
    text_report = "\n".join(lines)
    
    # Save to file if output directory is provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cooling_report_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(text_report)
        
        return filepath
    
    return text_report


def generate_html_report(result, output_dir=None):
    """
    Generate an HTML report
    
    Args:
        result (dict): Calculation result
        output_dir (str, optional): Directory to save report file
        
    Returns:
        str: HTML report or file path
    """
    # Generate basic HTML structure
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html>")
    html.append("<head>")
    html.append("  <title>Data Center Cooling Calculation Report</title>")
    html.append("  <style>")
    html.append("    body { font-family: Arial, sans-serif; margin: 20px; }")
    html.append("    h1 { color: #2c3e50; text-align: center; }")
    html.append("    h2 { color: #3498db; border-bottom: 1px solid #3498db; padding-bottom: 5px; }")
    html.append("    .container { max-width: 1000px; margin: 0 auto; }")
    html.append("    .section { margin-bottom: 20px; }")
    html.append("    table { width: 100%; border-collapse: collapse; }")
    html.append("    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }")
    html.append("    th { background-color: #f2f2f2; }")
    html.append("    .warning { color: #e74c3c; }")
    html.append("  </style>")
    html.append("</head>")
    html.append("<body>")
    html.append("  <div class='container'>")
    
    # Add header
    html.append(f"    <h1>Data Center Cooling Calculation Report</h1>")
    html.append(f"    <p style='text-align: center;'>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
    
    # Add input parameters
    html.append("    <div class='section'>")
    html.append("      <h2>Input Parameters</h2>")
    html.append("      <table>")
    html.append("        <tr><th>Parameter</th><th>Value</th></tr>")
    
    if "input_parameters" in result:
        params = result["input_parameters"]
        html.append(f"        <tr><td>Cooling Capacity</td><td>{params.get('cooling_kw', 'N/A'):.1f} kW</td></tr>")
        html.append(f"        <tr><td>Room Temperature</td><td>{params.get('room_temp', 'N/A'):.1f} °C</td></tr>")
        html.append(f"        <tr><td>Desired Temperature</td><td>{params.get('desired_temp', 'N/A'):.1f} °C</td></tr>")
        html.append(f"        <tr><td>Water Temperature</td><td>{params.get('water_temp', 'N/A'):.1f} °C</td></tr>")
        html.append(f"        <tr><td>Fluid Type</td><td>{params.get('fluid_type', 'water')}</td></tr>")
        html.append(f"        <tr><td>Glycol Percentage</td><td>{params.get('glycol_percentage', 0)}%</td></tr>")
    
    html.append("      </table>")
    html.append("    </div>")
    
    # Add product information
    html.append("    <div class='section'>")
    html.append("      <h2>Recommended Product</h2>")
    
    if "product" in result and result["product"]:
        product = result["product"]
        html.append("      <table>")
        html.append("        <tr><th>Property</th><th>Value</th></tr>")
        html.append(f"        <tr><td>Product</td><td>{product.get('name', 'N/A')}</td></tr>")
        html.append(f"        <tr><td>Series</td><td>{product.get('series', 'N/A')}</td></tr>")
        html.append(f"        <tr><td>Description</td><td>{product.get('description', 'N/A')}</td></tr>")
        html.append(f"        <tr><td>Max Cooling Capacity</td><td>{product.get('max_cooling_capacity', 'N/A'):.1f} kW</td></tr>")
        html.append("      </table>")
    else:
        html.append("      <p>No product recommendation available.</p>")
    
    html.append("    </div>")
    
    # Add results in a 2-column layout
    html.append("    <div class='section'>")
    html.append("      <h2>Calculation Results</h2>")
    html.append("      <table>")
    html.append("        <tr>")
    html.append("          <td style='width: 50%; vertical-align: top;'>")
    
    # Water side results
    html.append("            <h3>Water Side</h3>")
    html.append("            <table>")
    html.append("              <tr><th>Parameter</th><th>Value</th></tr>")
    
    if "water_side" in result:
        water = result["water_side"]
        html.append(f"              <tr><td>Flow Rate</td><td>{water.get('flow_rate', 'N/A'):.2f} m³/h</td></tr>")
        html.append(f"              <tr><td>Pressure Drop</td><td>{water.get('pressure_drop', 'N/A'):.1f} kPa</td></tr>")
        html.append(f"              <tr><td>Pump Power</td><td>{water.get('pump_power', 'N/A'):.3f} kW</td></tr>")
        if "temperature_in" in water and "temperature_out" in water:
            html.append(f"              <tr><td>Inlet Temperature</td><td>{water.get('temperature_in', 'N/A'):.1f} °C</td></tr>")
            html.append(f"              <tr><td>Outlet Temperature</td><td>{water.get('temperature_out', 'N/A'):.1f} °C</td></tr>")
            html.append(f"              <tr><td>Temperature Difference</td><td>{water.get('delta_t', 'N/A'):.1f} °C</td></tr>")
    
    html.append("            </table>")
    html.append("          </td>")
    html.append("          <td style='width: 50%; vertical-align: top;'>")
    
    # Air side results
    html.append("            <h3>Air Side</h3>")
    html.append("            <table>")
    html.append("              <tr><th>Parameter</th><th>Value</th></tr>")
    
    if "air_side" in result:
        air = result["air_side"]
        html.append(f"              <tr><td>Air Flow Rate</td><td>{air.get('flow_rate', 'N/A'):.1f} m³/h</td></tr>")
        html.append(f"              <tr><td>Fan Speed</td><td>{air.get('fan_speed_percentage', 'N/A'):.1f}%</td></tr>")
        html.append(f"              <tr><td>Fan Power</td><td>{air.get('fan_power', 'N/A'):.3f} kW</td></tr>")
        if "temperature_in" in air and "temperature_out" in air:
            html.append(f"              <tr><td>Inlet Temperature</td><td>{air.get('temperature_in', 'N/A'):.1f} °C</td></tr>")
            html.append(f"              <tr><td>Outlet Temperature</td><td>{air.get('temperature_out', 'N/A'):.1f} °C</td></tr>")
            html.append(f"              <tr><td>Temperature Difference</td><td>{air.get('delta_t', 'N/A'):.1f} °C</td></tr>")
    
    html.append("            </table>")
    html.append("          </td>")
    html.append("        </tr>")
    html.append("      </table>")
    html.append("    </div>")
    
    # Add efficiency results
    if "efficiency" in result:
        html.append("    <div class='section'>")
        html.append("      <h2>Efficiency Metrics</h2>")
        html.append("      <table>")
        html.append("        <tr><th>Metric</th><th>Value</th></tr>")
        
        eff = result["efficiency"]
        html.append(f"        <tr><td>Coefficient of Performance (COP)</td><td>{eff.get('cop', 'N/A'):.1f}</td></tr>")
        html.append(f"        <tr><td>Energy Efficiency Ratio (EER)</td><td>{eff.get('eer', 'N/A'):.1f}</td></tr>")
        html.append(f"        <tr><td>Total Power Consumption</td><td>{eff.get('total_power', 'N/A'):.3f} kW</td></tr>")
        
        html.append("      </table>")
        html.append("    </div>")
    
    # Add heat transfer results
    if "heat_transfer" in result:
        html.append("    <div class='section'>")
        html.append("      <h2>Heat Transfer Details</h2>")
        html.append("      <table>")
        html.append("        <tr><th>Parameter</th><th>Value</th></tr>")
        
        heat = result["heat_transfer"]
        html.append(f"        <tr><td>Actual Cooling Capacity</td><td>{heat.get('cooling_capacity', 'N/A'):.1f} kW</td></tr>")
        html.append(f"        <tr><td>Heat Exchanger Effectiveness</td><td>{heat.get('effectiveness', 'N/A'):.3f}</td></tr>")
        html.append(f"        <tr><td>Log Mean Temperature Difference</td><td>{heat.get('lmtd', 'N/A'):.1f} °C</td></tr>")
        html.append(f"        <tr><td>UA Value</td><td>{heat.get('ua_value', 'N/A'):.1f} kW/K</td></tr>")
        
        html.append("      </table>")
        html.append("    </div>")
    
    # Add commercial results
    if "commercial" in result:
        html.append("    <div class='section'>")
        html.append("      <h2>Commercial Analysis</h2>")
        
        comm = result["commercial"]
        
        # Capital costs
        if "capital_costs" in comm:
            html.append("      <h3>Capital Costs</h3>")
            html.append("      <table>")
            html.append("        <tr><th>Item</th><th>Cost</th></tr>")
            
            cap = comm["capital_costs"]
            html.append(f"        <tr><td>Product</td><td>${cap.get('product', 'N/A'):,.2f}</td></tr>")
            html.append(f"        <tr><td>Installation</td><td>${cap.get('installation', 'N/A'):,.2f}</td></tr>")
            html.append(f"        <tr><td><strong>Total Capital</strong></td><td><strong>${cap.get('total', 'N/A'):,.2f}</strong></td></tr>")
            
            html.append("      </table>")
        
        # Operational costs
        if "operational_costs" in comm:
            html.append("      <h3>Annual Operational Costs</h3>")
            html.append("      <table>")
            html.append("        <tr><th>Item</th><th>Cost</th></tr>")
            
            op = comm["operational_costs"]
            html.append(f"        <tr><td>Electricity</td><td>${op.get('annual_electricity', 'N/A'):,.2f}</td></tr>")
            html.append(f"        <tr><td>Maintenance</td><td>${op.get('annual_maintenance', 'N/A'):,.2f}</td></tr>")
            html.append(f"        <tr><td><strong>Total Operational</strong></td><td><strong>${op.get('annual_total', 'N/A'):,.2f}</strong></td></tr>")
            html.append(f"        <tr><td>Annual Savings</td><td><span style='color: green;'>${op.get('annual_savings', 'N/A'):,.2f}</span></td></tr>")
            
            html.append("      </table>")
        
        # ROI
        if "roi" in comm:
            html.append("      <h3>Return on Investment</h3>")
            html.append("      <table>")
            html.append("        <tr><th>Metric</th><th>Value</th></tr>")
            
            roi = comm["roi"]
            html.append(f"        <tr><td>Simple Payback Period</td><td>{roi.get('simple_payback_years', 'N/A'):.1f} years</td></tr>")
            html.append(f"        <tr><td>Annual ROI</td><td>{roi.get('annual_roi_percentage', 'N/A'):.1f}%</td></tr>")
            
            html.append("      </table>")
        
        # TCO
        if "tco" in comm:
            html.append("      <h3>Total Cost of Ownership (10 years)</h3>")
            html.append("      <table>")
            html.append("        <tr><th>Item</th><th>Cost</th></tr>")
            
            tco = comm["tco"]
            html.append(f"        <tr><td>Capital Expenditure</td><td>${tco.get('capex', 'N/A'):,.2f}</td></tr>")
            html.append(f"        <tr><td>Operational Expenditure</td><td>${tco.get('opex', 'N/A'):,.2f}</td></tr>")
            html.append(f"        <tr><td><strong>Total TCO</strong></td><td><strong>${tco.get('total', 'N/A'):,.2f}</strong></td></tr>")
            html.append(f"        <tr><td>Traditional Solution TCO</td><td>${tco.get('traditional_total', 'N/A'):,.2f}</td></tr>")
            html.append(f"        <tr><td>TCO Savings</td><td><span style='color: green;'>${tco.get('savings', 'N/A'):,.2f}</span></td></tr>")
            
            html.append("      </table>")
        
        # Environmental
        if "environmental" in comm:
            html.append("      <h3>Environmental Impact</h3>")
            html.append("      <table>")
            html.append("        <tr><th>Metric</th><th>Value</th></tr>")
            
            env = comm["environmental"]
            html.append(f"        <tr><td>Annual Energy Savings</td><td>{env.get('annual_energy_savings_kwh', 'N/A'):,.1f} kWh</td></tr>")
            html.append(f"        <tr><td>Annual CO2 Reduction</td><td>{env.get('annual_carbon_reduction_kg', 'N/A'):,.1f} kg</td></tr>")
            html.append(f"        <tr><td>Lifetime CO2 Reduction</td><td>{env.get('lifetime_carbon_reduction_kg', 'N/A'):,.1f} kg</td></tr>")
            
            html.append("      </table>")
        
        html.append("    </div>")
    
    # Add warnings
    if "warnings" in result and result["warnings"]:
        html.append("    <div class='section'>")
        html.append("      <h2>Warnings</h2>")
        html.append("      <ul class='warning'>")
        
        for warning in result["warnings"]:
            html.append(f"        <li>{warning}</li>")
        
        html.append("      </ul>")
        html.append("    </div>")
    
    # Add footer
    html.append("    <div style='text-align: center; margin-top: 30px; color: #7f8c8d;'>")
    html.append("      <p>Generated by Data Center Cooling Calculator v0.1.0</p>")
    html.append("    </div>")
    
    # Close tags
    html.append("  </div>")
    html.append("</body>")
    html.append("</html>")
    
    # Join all HTML lines
    html_report = "\n".join(html)
    
    # Save to file if output directory is provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cooling_report_{timestamp}.html"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(html_report)
        
        return filepath
    
    return html_report 