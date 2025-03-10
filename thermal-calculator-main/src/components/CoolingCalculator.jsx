// src/components/CoolingCalculator.jsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import { Download, RefreshCw, Settings, Save, FileText, PlusCircle, MinusCircle } from 'lucide-react';

// Main calculator component
const CoolingCalculator = () => {
  // Main required inputs
  const [coolingRequired, setCoolingRequired] = useState(50); // kW
  const [roomTemp, setRoomTemp] = useState(24); // °C
  const [desiredTemp, setDesiredTemp] = useState(22); // °C
  const [waterTemp, setWaterTemp] = useState(15); // °C
  
  // Optional parameters with default values
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [location, setLocation] = useState('europe');
  const [altitude, setAltitude] = useState(0); // meters
  const [fluidType, setFluidType] = useState('water');
  const [glycolPercentage, setGlycolPercentage] = useState(0);
  const [rackType, setRackType] = useState('');
  const [pipeConfig, setPipeConfig] = useState('bottom_fed');
  const [voltage, setVoltage] = useState(230);
  
  // Units
  const [units, setUnits] = useState('metric');

  // Results state
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('technical');

  // Product options
  const rackOptions = [
    { value: '', label: 'Auto Select' },
    { value: '42U600', label: '42U 600mm Wide Rack' },
    { value: '42U800', label: '42U 800mm Wide Rack' },
    { value: '48U800', label: '48U 800mm Wide Rack' }
  ];

  // Handle calculation
  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Prepare the request payload
      const payload = {
        cooling_kw: parseFloat(coolingRequired),
        room_temp: parseFloat(roomTemp),
        desired_temp: parseFloat(desiredTemp),
        water_temp: parseFloat(waterTemp),
        location,
        altitude: parseFloat(altitude),
        fluid_type: fluidType,
        glycol_percentage: parseFloat(glycolPercentage),
        rack_type: rackType,
        pipe_configuration: pipeConfig,
        voltage: parseFloat(voltage),
        units
      };
      
      // Make API call
      const response = await fetch('/api/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle export to PDF/Excel
  const handleExport = (format) => {
    if (!results) return;
    
    // Implementation would typically use a library like jspdf or xlsx
    alert(`Exporting results in ${format} format...`);
  };

  // Reset all inputs to defaults
  const handleReset = () => {
    setCoolingRequired(50);
    setRoomTemp(24);
    setDesiredTemp(22);
    setWaterTemp(15);
    setLocation('europe');
    setAltitude(0);
    setFluidType('water');
    setGlycolPercentage(0);
    setRackType('');
    setPipeConfig('bottom_fed');
    setVoltage(230);
    setUnits('metric');
    setResults(null);
    setError(null);
  };

  return (
    <div className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Data Center Cooling Calculator</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Input Section */}
            <div className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Required Parameters</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cooling-required">
                      Cooling Required ({units === 'metric' ? 'kW' : 'tons'})
                    </Label>
                    <Input
                      id="cooling-required"
                      type="number"
                      value={coolingRequired}
                      onChange={(e) => setCoolingRequired(e.target.value)}
                      min="0"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="room-temp">
                      Room Temperature ({units === 'metric' ? '°C' : '°F'})
                    </Label>
                    <Input
                      id="room-temp"
                      type="number"
                      value={roomTemp}
                      onChange={(e) => setRoomTemp(e.target.value)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="desired-temp">
                      Desired Temperature ({units === 'metric' ? '°C' : '°F'})
                    </Label>
                    <Input
                      id="desired-temp"
                      type="number"
                      value={desiredTemp}
                      onChange={(e) => setDesiredTemp(e.target.value)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="water-temp">
                      Supply Water Temperature ({units === 'metric' ? '°C' : '°F'})
                    </Label>
                    <Input
                      id="water-temp"
                      type="number"
                      value={waterTemp}
                      onChange={(e) => setWaterTemp(e.target.value)}
                    />
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setAdvancedOpen(!advancedOpen)}
                  className="flex items-center"
                >
                  {advancedOpen ? <MinusCircle className="h-4 w-4 mr-2" /> : <PlusCircle className="h-4 w-4 mr-2" />}
                  {advancedOpen ? 'Hide Advanced Options' : 'Show Advanced Options'}
                </Button>
                
                <div className="flex items-center space-x-2 ml-auto">
                  <Label htmlFor="units">Units:</Label>
                  <Select value={units} onValueChange={setUnits}>
                    <SelectTrigger id="units" className="w-32">
                      <SelectValue placeholder="Select units" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="metric">Metric</SelectItem>
                      <SelectItem value="imperial">Imperial</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {advancedOpen && (
                <div className="space-y-4 border p-4 rounded-md">
                  <h3 className="text-lg font-medium">Advanced Parameters</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="location">Location</Label>
                      <Select value={location} onValueChange={setLocation}>
                        <SelectTrigger id="location">
                          <SelectValue placeholder="Select location" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="europe">Europe</SelectItem>
                          <SelectItem value="north_america">North America</SelectItem>
                          <SelectItem value="nordic">Nordic</SelectItem>
                          <SelectItem value="asia_pacific">Asia Pacific</SelectItem>
                          <SelectItem value="singapore">Singapore</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="altitude">
                        Altitude ({units === 'metric' ? 'm' : 'ft'})
                      </Label>
                      <Input
                        id="altitude"
                        type="number"
                        value={altitude}
                        onChange={(e) => setAltitude(e.target.value)}
                        min="0"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="fluid-type">Fluid Type</Label>
                      <Select value={fluidType} onValueChange={setFluidType}>
                        <SelectTrigger id="fluid-type">
                          <SelectValue placeholder="Select fluid type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="water">Water</SelectItem>
                          <SelectItem value="ethylene_glycol">Ethylene Glycol</SelectItem>
                          <SelectItem value="propylene_glycol">Propylene Glycol</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    {fluidType !== 'water' && (
                      <div className="space-y-2">
                        <Label htmlFor="glycol-percentage">Glycol Percentage (%)</Label>
                        <div className="flex items-center space-x-4">
                          <Slider
                            id="glycol-percentage"
                            min={0}
                            max={60}
                            step={5}
                            value={[glycolPercentage]}
                            onValueChange={(value) => setGlycolPercentage(value[0])}
                            className="flex-1"
                          />
                          <span className="w-8 text-center">{glycolPercentage}%</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="space-y-2">
                      <Label htmlFor="rack-type">Rack Type</Label>
                      <Select value={rackType} onValueChange={setRackType}>
                        <SelectTrigger id="rack-type">
                          <SelectValue placeholder="Select rack type" />
                        </SelectTrigger>
                        <SelectContent>
                          {rackOptions.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="pipe-config">Pipe Configuration</Label>
                      <Select value={pipeConfig} onValueChange={setPipeConfig}>
                        <SelectTrigger id="pipe-config">
                          <SelectValue placeholder="Select pipe configuration" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="bottom_fed">Bottom Fed</SelectItem>
                          <SelectItem value="top_fed">Top Fed</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="voltage">Voltage (V)</Label>
                      <Select value={voltage} onValueChange={setVoltage}>
                        <SelectTrigger id="voltage">
                          <SelectValue placeholder="Select voltage" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="208">208V (US)</SelectItem>
                          <SelectItem value="230">230V (EU)</SelectItem>
                          <SelectItem value="240">240V</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="flex space-x-3 pt-4">
                <Button 
                  onClick={handleCalculate} 
                  disabled={loading}
                  className="flex-1"
                >
                  {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : 'Calculate'}
                </Button>
                <Button 
                  variant="outline" 
                  onClick={handleReset}
                  className="flex items-center"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reset
                </Button>
              </div>
              
              {error && (
                <Alert variant="destructive" className="mt-4">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </div>
            
            {/* Results Section */}
            <div>
              {results ? (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium">Results</h3>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm" onClick={() => handleExport('pdf')}>
                        <FileText className="h-4 w-4 mr-2" />
                        PDF
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleExport('excel')}>
                        <Download className="h-4 w-4 mr-2" />
                        Excel
                      </Button>
                    </div>
                  </div>
                  
                  <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList className="grid grid-cols-3">
                      <TabsTrigger value="technical">Technical</TabsTrigger>
                      <TabsTrigger value="commercial">Commercial</TabsTrigger>
                      <TabsTrigger value="environmental">Environmental</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="technical" className="space-y-4">
                      <ResultsSummary results={results} />
                      
                      <TechnicalResults 
                        results={results}
                        units={units}
                      />
                    </TabsContent>
                    
                    <TabsContent value="commercial" className="space-y-4">
                      {results.commercial ? (
                        <CommercialResults 
                          results={results.commercial}
                          units={units}
                        />
                      ) : (
                        <p>Commercial results not available.</p>
                      )}
                    </TabsContent>
                    
                    <TabsContent value="environmental" className="space-y-4">
                      {results.commercial?.environmental ? (
                        <EnvironmentalResults 
                          results={results.commercial.environmental}
                          units={units}
                        />
                      ) : (
                        <p>Environmental results not available.</p>
                      )}
                    </TabsContent>
                  </Tabs>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full space-y-4 p-8 text-center">
                  <Settings className="h-16 w-16 text-gray-300" />
                  <p className="text-gray-500">
                    Enter the required parameters and click 'Calculate' to see results.
                  </p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Component for displaying a summary of the results
const ResultsSummary = ({ results }) => {
  if (!results) return null;
  
  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Recommended Product</span>
            <span className="font-medium">
              {results.product?.name || 'Not Available'}
            </span>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Cooling Capacity</span>
            <span className="font-medium">
              {results.cooling_capacity} kW
            </span>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Water Flow Rate</span>
            <span className="font-medium">
              {results.water_side?.flow_rate.toFixed(2)} m³/h
            </span>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Fan Speed</span>
            <span className="font-medium">
              {results.air_side?.fan_speed_percentage.toFixed(1)}%
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Component for displaying technical results
const TechnicalResults = ({ results, units }) => {
  if (!results) return null;
  
  const waterSide = results.water_side || {};
  const airSide = results.air_side || {};
  const valveRecommendation = results.valve_recommendation || {};
  
  // Generate chart data for water parameters
  const waterChartData = [
    { name: 'Supply Temperature', value: waterSide.supply_temp },
    { name: 'Return Temperature', value: waterSide.return_temp },
    { name: 'Delta T', value: waterSide.delta_t }
  ];
  
  // Generate chart data for air flow vs fan speed
  const fanChartData = [
    { name: 'Fan Speed (%)', value: airSide.fan_speed_percentage },
    { name: 'Power (W)', value: airSide.power_consumption / 10 },  // Scaled for visualization
    { name: 'Noise (dB)', value: airSide.noise_level }
  ];
  
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Water Side Parameters */}
        <Card>
          <CardHeader>
            <CardTitle>Water Side Parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                <div className="text-sm text-gray-500">Flow Rate:</div>
                <div className="text-sm font-medium text-right">
                  {waterSide.flow_rate?.toFixed(2)} m³/h
                </div>
                
                <div className="text-sm text-gray-500">Supply Temperature:</div>
                <div className="text-sm font-medium text-right">
                  {waterSide.supply_temp?.toFixed(1)} °C
                </div>
                
                <div className="text-sm text-gray-500">Return Temperature:</div>
                <div className="text-sm font-medium text-right">
                  {waterSide.return_temp?.toFixed(1)} °C
                </div>
                
                <div className="text-sm text-gray-500">Temperature Difference:</div>
                <div className="text-sm font-medium text-right">
                  {waterSide.delta_t?.toFixed(1)} °C
                </div>
                
                <div className="text-sm text-gray-500">Pressure Drop:</div>
                <div className="text-sm font-medium text-right">
                  {waterSide.pressure_drop?.toFixed(2)} kPa
                </div>
                
                <div className="text-sm text-gray-500">Fluid Type:</div>
                <div className="text-sm font-medium text-right">
                  {waterSide.fluid_type || 'Water'}
                  {waterSide.glycol_percentage > 0 && ` (${waterSide.glycol_percentage}% Glycol)`}
                </div>
              </div>
              
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={waterChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        
        {/* Air Side Parameters */}
        <Card>
          <CardHeader>
            <CardTitle>Air Side Parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                <div className="text-sm text-gray-500">Air Flow:</div>
                <div className="text-sm font-medium text-right">
                  {airSide.air_flow?.toFixed(0)} m³/h
                </div>
                
                <div className="text-sm text-gray-500">Static Pressure:</div>
                <div className="text-sm font-medium text-right">
                  {airSide.static_pressure?.toFixed(1)} Pa
                </div>
                
                <div className="text-sm text-gray-500">Fan Speed:</div>
                <div className="text-sm font-medium text-right">
                  {airSide.fan_speed_percentage?.toFixed(1)}%
                </div>
                
                <div className="text-sm text-gray-500">Power Consumption:</div>
                <div className="text-sm font-medium text-right">
                  {airSide.power_consumption?.toFixed(1)} W
                </div>
                
                <div className="text-sm text-gray-500">Noise Level:</div>
                <div className="text-sm font-medium text-right">
                  {airSide.noise_level?.toFixed(1)} dB(A)
                </div>
                
                <div className="text-sm text-gray-500">Number of Fans:</div>
                <div className="text-sm font-medium text-right">
                  {airSide.number_of_fans || 'N/A'}
                </div>
              </div>
              
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={fanChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Valve Recommendation */}
      <Card>
        <CardHeader>
          <CardTitle>Valve Recommendation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="text-sm text-gray-500">Recommended Valve:</div>
              <div className="text-lg font-medium">
                {valveRecommendation.valve_type || 'N/A'} {valveRecommendation.valve_size || 'N/A'}
              </div>
              <div className="text-sm">
                {valveRecommendation.sufficient ? 
                  'This valve is sufficient for the required flow rate.' :
                  'This valve may not be sufficient. Consider a larger size.'}
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm text-gray-500">Valve Parameters:</div>
              <div className="grid grid-cols-2 gap-1">
                <div className="text-sm text-gray-500">Max Flow Rate:</div>
                <div className="text-sm font-medium">
                  {valveRecommendation.max_flow_rate?.toFixed(1)} m³/h
                </div>
                
                <div className="text-sm text-gray-500">Utilization:</div>
                <div className="text-sm font-medium">
                  {valveRecommendation.utilization_percentage?.toFixed(1)}%
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm text-gray-500">Recommended Settings:</div>
              <div className="grid grid-cols-2 gap-1">
                <div className="text-sm text-gray-500">Nominal:</div>
                <div className="text-sm font-medium">
                  {valveRecommendation.recommended_settings?.nominal?.toFixed(1)}%
                </div>
                
                <div className="text-sm text-gray-500">Min:</div>
                <div className="text-sm font-medium">
                  {valveRecommendation.recommended_settings?.min?.toFixed(1)}%
                </div>
                
                <div className="text-sm text-gray-500">Max:</div>
                <div className="text-sm font-medium">
                  {valveRecommendation.recommended_settings?.max?.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* System Efficiency */}
      <Card>
        <CardHeader>
          <CardTitle>System Efficiency</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-sm text-gray-500 mb-2">COP</div>
              <div className="text-3xl font-bold">
                {results.efficiency?.cop?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Coefficient of Performance
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-gray-500 mb-2">EER</div>
              <div className="text-3xl font-bold">
                {results.efficiency?.eer?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Energy Efficiency Ratio
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-gray-500 mb-2">Water Efficiency</div>
              <div className="text-3xl font-bold">
                {results.efficiency?.water_efficiency?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Water-side Efficiency Factor
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Component for displaying commercial results
const CommercialResults = ({ results, units }) => {
  if (!results) return null;
  
  const tco = results.tco || {};
  const roi = results.roi || {};
  
  // Generate chart data for TCO breakdown
  const tcoChartData = [
    { name: 'Capital Cost', value: tco.capital_cost },
    { name: 'Energy Cost', value: tco.lifetime_energy_cost },
    { name: 'Maintenance', value: tco.lifetime_maintenance }
  ];
  
  // Generate chart data for annual energy consumption
  const energyChartData = Array.from({ length: 12 }, (_, i) => ({
    name: `Month ${i + 1}`,
    energy: tco.annual_energy_consumption / 12
  }));
  
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28'];
  
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Total Cost of Ownership</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <div className="text-sm text-gray-500">Total Cost:</div>
                  <div className="text-sm font-medium text-right">
                    ${tco.total_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  
                  <div className="text-sm text-gray-500">Capital Cost:</div>
                  <div className="text-sm font-medium text-right">
                    ${tco.capital_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  
                  <div className="text-sm text-gray-500">Annual Energy Cost:</div>
                  <div className="text-sm font-medium text-right">
                    ${tco.annual_energy_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  
                  <div className="text-sm text-gray-500">Lifetime Energy Cost:</div>
                  <div className="text-sm font-medium text-right">
                    ${tco.lifetime_energy_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  
                  <div className="text-sm text-gray-500">Annual Maintenance:</div>
                  <div className="text-sm font-medium text-right">
                    ${tco.annual_maintenance?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  
                  <div className="text-sm text-gray-500">Lifetime Maintenance:</div>
                  <div className="text-sm font-medium text-right">
                    ${tco.lifetime_maintenance?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  
                  <div className="text-sm text-gray-500">Payback Period:</div>
                  <div className="text-sm font-medium text-right">
                    {tco.payback_period?.toFixed(1)} years
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={tcoChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {tcoChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {roi && (
        <Card>
          <CardHeader>
            <CardTitle>Return on Investment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <div className="text-sm text-gray-500">ROI Percentage:</div>
                  <div className="text-sm font-medium text-right">
                    {roi.roi_percentage?.toFixed(1)}%
                  </div>
                  
                  <div className="text-sm text-gray-500">Lifetime Savings:</div>
                  <div className="text-sm font-medium text-right">
                    ${roi.lifetime_savings?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  
                  <div className="text-sm text-gray-500">Annual Savings:</div>
                  <div className="text-sm font-medium text-right">
                    ${roi.annual_savings?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  
                  <div className="text-sm text-gray-500">Payback Period:</div>
                  <div className="text-sm font-medium text-right">
                    {roi.payback_period?.toFixed(1)} years
                  </div>
                </div>
              </div>
              
              <div>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={energyChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(value) => `${value.toLocaleString()} kWh`} />
                    <Line type="monotone" dataKey="energy" stroke="#8884d8" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Component for displaying environmental results
const EnvironmentalResults = ({ results, units }) => {
  if (!results) return null;
  
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Environmental Impact</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                <div className="text-sm text-gray-500">Annual Energy Consumption:</div>
                <div className="text-sm font-medium text-right">
                  {results.annual_energy?.toLocaleString()} kWh
                </div>
                
                <div className="text-sm text-gray-500">Annual Carbon Emissions:</div>
                <div className="text-sm font-medium text-right">
                  {results.annual_carbon?.toLocaleString()} kg CO₂
                </div>
                
                <div className="text-sm text-gray-500">Lifetime Carbon Emissions:</div>
                <div className="text-sm font-medium text-right">
                  {results.lifetime_carbon?.toLocaleString()} kg CO₂
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="text-center p-4 bg-green-50 rounded-md">
                <div className="text-sm text-gray-500 mb-2">
                  Carbon Offset Equivalents
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(results.tree_equivalent).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500">
                      Trees planted
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(results.car_equivalent).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500">
                      Cars removed for a year
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Energy Efficiency Rating</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-md bg-gray-200 rounded-full h-4 mb-4">
              <div 
                className="bg-green-500 h-4 rounded-full"
                style={{ width: `${Math.min(results.efficiency_rating * 20, 100)}%` }}
              ></div>
            </div>
            <div className="grid grid-cols-5 w-full max-w-md text-xs text-center">
              <div>Very Poor</div>
              <div>Poor</div>
              <div>Average</div>
              <div>Good</div>
              <div>Excellent</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CoolingCalculator;
