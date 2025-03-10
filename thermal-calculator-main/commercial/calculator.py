"""
Commercial calculations for the Data Center Cooling Calculator.
"""


class CommercialCalculator:
    """
    Commercial calculator that provides business metrics such as
    ROI, TCO, and energy savings for cooling solutions.
    """
    
    def __init__(self):
        """Initialize the commercial calculator"""
        # Default values for calculations
        self.electricity_cost = 0.15  # $/kWh
        self.maintenance_cost_percentage = 0.05  # 5% of capital cost per year
        self.traditional_cooling_cop = 3.0  # COP of traditional cooling systems
        self.carbon_factor = 0.5  # kg CO2e per kWh
        self.expected_lifetime = 10  # years
        
    def calculate(self, cooling_kw, product, result):
        """
        Perform commercial calculations
        
        Args:
            cooling_kw (float): Required cooling capacity in kW
            product (dict): Product specifications
            result (dict): Technical calculation results
            
        Returns:
            dict: Commercial calculation results
        """
        # Initialize results dictionary
        commercial_results = {
            "capital_costs": {},
            "operational_costs": {},
            "roi": {},
            "tco": {},
            "environmental": {}
        }
        
        # Calculate capital costs
        product_cost = self.calculate_product_cost(product)
        installation_cost = product_cost * 0.2  # Assume installation is 20% of product cost
        
        commercial_results["capital_costs"]["product"] = product_cost
        commercial_results["capital_costs"]["installation"] = installation_cost
        commercial_results["capital_costs"]["total"] = product_cost + installation_cost
        
        # Calculate operational costs
        annual_hours = 8760  # hours in a year
        traditional_power = cooling_kw / self.traditional_cooling_cop
        solution_power = result["efficiency"]["total_power"]
        
        annual_electricity_traditional = traditional_power * annual_hours * self.electricity_cost
        annual_electricity_solution = solution_power * annual_hours * self.electricity_cost
        annual_savings = annual_electricity_traditional - annual_electricity_solution
        
        annual_maintenance = product_cost * self.maintenance_cost_percentage
        
        commercial_results["operational_costs"]["annual_electricity"] = annual_electricity_solution
        commercial_results["operational_costs"]["annual_maintenance"] = annual_maintenance
        commercial_results["operational_costs"]["annual_total"] = (
            annual_electricity_solution + annual_maintenance
        )
        commercial_results["operational_costs"]["annual_savings"] = annual_savings
        
        # Calculate ROI
        if annual_savings > 0:
            simple_payback_years = (product_cost + installation_cost) / annual_savings
            roi_percentage = (annual_savings / (product_cost + installation_cost)) * 100
        else:
            simple_payback_years = float('inf')
            roi_percentage = 0
        
        commercial_results["roi"]["simple_payback_years"] = simple_payback_years
        commercial_results["roi"]["annual_roi_percentage"] = roi_percentage
        
        # Calculate TCO (Total Cost of Ownership)
        tco_years = min(self.expected_lifetime, 10)  # Cap at 10 years for TCO calculation
        
        capex = product_cost + installation_cost
        opex = commercial_results["operational_costs"]["annual_total"] * tco_years
        tco = capex + opex
        
        traditional_opex = annual_electricity_traditional * tco_years
        traditional_capex = product_cost * 0.8  # Assume traditional solution costs 80% of new solution
        traditional_tco = traditional_capex + traditional_opex
        
        tco_savings = traditional_tco - tco
        
        commercial_results["tco"]["capex"] = capex
        commercial_results["tco"]["opex"] = opex
        commercial_results["tco"]["total"] = tco
        commercial_results["tco"]["traditional_total"] = traditional_tco
        commercial_results["tco"]["savings"] = tco_savings
        
        # Calculate environmental impact
        annual_energy_savings_kwh = (traditional_power - solution_power) * annual_hours
        annual_carbon_reduction = annual_energy_savings_kwh * self.carbon_factor
        lifetime_carbon_reduction = annual_carbon_reduction * self.expected_lifetime
        
        commercial_results["environmental"]["annual_energy_savings_kwh"] = annual_energy_savings_kwh
        commercial_results["environmental"]["annual_carbon_reduction_kg"] = annual_carbon_reduction
        commercial_results["environmental"]["lifetime_carbon_reduction_kg"] = lifetime_carbon_reduction
        
        # Add any incentives or rebates (simplified)
        if annual_carbon_reduction > 10000:  # Arbitrary threshold
            commercial_results["roi"]["eligible_for_incentives"] = True
            commercial_results["roi"]["potential_incentives"] = annual_carbon_reduction * 0.01  # $0.01 per kg CO2
        else:
            commercial_results["roi"]["eligible_for_incentives"] = False
            commercial_results["roi"]["potential_incentives"] = 0
        
        return commercial_results
    
    def calculate_product_cost(self, product):
        """
        Estimate product cost based on specifications
        
        Args:
            product (dict): Product specifications
            
        Returns:
            float: Estimated product cost in USD
        """
        # Base cost determined by product series
        if product["series"] == "CL20":
            base_cost = 15000
        elif product["series"] == "CL21":
            base_cost = 8000  # Passive solution is less expensive
        elif product["series"] == "CL23":
            base_cost = 25000  # High-performance solution is more expensive
        else:
            base_cost = 15000  # Default
        
        # Adjust cost based on cooling capacity
        capacity_factor = product["max_cooling_capacity"] / 50  # Normalize to 50kW
        
        # Calculate final cost with some non-linearity (square root for economies of scale)
        product_cost = base_cost * (capacity_factor ** 0.7)
        
        return product_cost 