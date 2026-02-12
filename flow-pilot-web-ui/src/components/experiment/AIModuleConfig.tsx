
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { 
  Mic, 
  Waves, 
  Settings, 
  Brain, 
  Target,
  Globe,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle
} from "lucide-react";
import { configurationService } from "@/services/configurationService";

interface AIModuleConfigProps {
  onConfigChange: (config: any) => void;
}

export function AIModuleConfig({ onConfigChange }: AIModuleConfigProps) {
  const [baseUrl, setBaseUrl] = useState("http://localhost:8000");
  const [connectionStatus, setConnectionStatus] = useState<Record<string, string>>({
    m1: "idle",
    m2: "idle", 
    m3: "idle",
    m4: "idle",
    m5: "idle"
  });

  // Module configurations
  const [moduleConfigs, setModuleConfigs] = useState({
    m1: {
      sensors: { endpoint: "/m1/sensors", method: "GET" },
      streaming: { endpoint: "/m1/streaming", method: "POST" },
      formatConversion: { endpoint: "/m1/format-conversion", method: "POST" },
      beamforming: { endpoint: "/m1/beamforming", method: "POST" },
      multiDevice: { endpoint: "/m1/multi-device", method: "POST" }
    },
    m2: {
      chunking: { endpoint: "/m2/chunking", method: "POST" },
      clickDetection: { endpoint: "/m2/click-detection", method: "POST" },
      noiseReduction: { endpoint: "/m2/noise-reduction", method: "POST" },
      filteringEnhancement: { endpoint: "/m2/filtering-enhancement", method: "POST" },
      qualityAssessment: { endpoint: "/m2/quality-assessment", method: "POST" }
    },
    m3: {
      pitchShift: { endpoint: "/m3/pitch-shift", method: "POST" },
      noiseInjection: { endpoint: "/m3/noise-injection", method: "POST" },
      timeStretch: { endpoint: "/m3/time-stretch", method: "POST" },
      volumeAdjustment: { endpoint: "/m3/volume-adjustment", method: "POST" },
      spectralAugmentation: { endpoint: "/m3/spectral-augmentation", method: "POST" },
      pipeline: { endpoint: "/m3/pipeline", method: "POST" }
    },
    m4: {
      featureExtraction: { endpoint: "/m4/feature-extraction", method: "POST" },
      trainModel: { endpoint: "/m4/train-model", method: "POST" },
      directionalInference: { endpoint: "/m4/directional-inference", method: "POST" },
      evaluate: { endpoint: "/m4/evaluate", method: "POST" },
      inference: { endpoint: "/m4/inference", method: "POST" },
      trainingStatus: { endpoint: "/m4/training-status", method: "GET" }
    },
    m5: {
      classification: { endpoint: "/m5/classification", method: "POST" },
      sceneAnalysis: { endpoint: "/m5/scene-analysis", method: "POST" },
      anomalyDetection: { endpoint: "/m5/anomaly-detection", method: "POST" },
      clustering: { endpoint: "/m5/clustering", method: "POST" },
      realTimeStart: { endpoint: "/m5/real-time-start", method: "POST" },
      realTimeStop: { endpoint: "/m5/real-time-stop", method: "POST" },
      results: { endpoint: "/m5/results", method: "GET" }
    }
  });

  const moduleInfo = [
    { id: "m1", name: "Data Acquisition", icon: Mic, description: "Sensors, streaming, beamforming" },
    { id: "m2", name: "Preprocessing", icon: Waves, description: "Chunking, click detection, filtering" },
    { id: "m3", name: "Data Augmentation", icon: Settings, description: "Pitch shift, noise injection, time stretch" },
    { id: "m4", name: "ML Processing", icon: Brain, description: "Feature extraction, model training, inference" },
    { id: "m5", name: "Applications", icon: Target, description: "Classification, scene analysis, clustering" }
  ];

  const updateEndpoint = (moduleId: string, functionName: string, field: string, value: string) => {
    setModuleConfigs(prev => ({
      ...prev,
      [moduleId]: {
        ...prev[moduleId as keyof typeof prev],
        [functionName]: {
          ...(prev[moduleId as keyof typeof prev] as any)[functionName],
          [field]: value
        }
      }
    }));
  };

  const testConnection = async (moduleId: string) => {
    setConnectionStatus(prev => ({ ...prev, [moduleId]: "testing" }));
    
    try {
      const response = await fetch(`${baseUrl}/health`);
      if (response.ok) {
        setConnectionStatus(prev => ({ ...prev, [moduleId]: "connected" }));
      } else {
        setConnectionStatus(prev => ({ ...prev, [moduleId]: "error" }));
      }
    } catch (error) {
      setConnectionStatus(prev => ({ ...prev, [moduleId]: "error" }));
    }
  };

  const testAllConnections = async () => {
    for (const module of moduleInfo) {
      await testConnection(module.id);
    }
  };

  const applyConfiguration = () => {
    const config = {
      baseUrl,
      modules: moduleConfigs
    };
    
    // Update the configuration service
    configurationService.updateBaseUrl(baseUrl);
    
    onConfigChange(config);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "testing":
        return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "connected":
        return "default";
      case "error":
        return "destructive";
      case "testing":
        return "secondary";
      default:
        return "outline";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">AI Module Configuration</h2>
          <p className="text-gray-600">Configure API endpoints for all acoustic AI modules</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={testAllConnections}>
            Test All Connections
          </Button>
          <Button onClick={applyConfiguration}>
            Apply Configuration
          </Button>
        </div>
      </div>

      {/* Base URL Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Base API Configuration
          </CardTitle>
          <CardDescription>Set the common base URL for all AI module endpoints</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="baseUrl">Base URL</Label>
            <Input
              id="baseUrl"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:8000"
            />
          </div>
          <p className="text-sm text-gray-500">
            This base URL will be used for all module endpoints. Example: {baseUrl}/m1/sensors
          </p>
        </CardContent>
      </Card>

      {/* Module Configurations */}
      <Tabs defaultValue="m1" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          {moduleInfo.map((module) => (
            <TabsTrigger key={module.id} value={module.id} className="flex items-center gap-2">
              <module.icon className="h-4 w-4" />
              {module.name}
            </TabsTrigger>
          ))}
        </TabsList>

        {moduleInfo.map((module) => (
          <TabsContent key={module.id} value={module.id}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <module.icon className="h-5 w-5" />
                    {module.name}
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(connectionStatus[module.id])}
                    <Badge variant={getStatusBadge(connectionStatus[module.id]) as any}>
                      {connectionStatus[module.id]}
                    </Badge>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => testConnection(module.id)}
                    >
                      Test Connection
                    </Button>
                  </div>
                </CardTitle>
                <CardDescription>{module.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(moduleConfigs[module.id as keyof typeof moduleConfigs]).map(([functionName, config]) => (
                    <div key={functionName} className="p-4 border rounded-lg space-y-3">
                      <h4 className="font-medium capitalize">{functionName.replace(/([A-Z])/g, ' $1').trim()}</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor={`${module.id}-${functionName}-endpoint`}>Endpoint</Label>
                          <Input
                            id={`${module.id}-${functionName}-endpoint`}
                            value={config.endpoint}
                            onChange={(e) => updateEndpoint(module.id, functionName, 'endpoint', e.target.value)}
                            placeholder={`/${module.id}/function-name`}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`${module.id}-${functionName}-method`}>HTTP Method</Label>
                          <Input
                            id={`${module.id}-${functionName}-method`}
                            value={config.method}
                            onChange={(e) => updateEndpoint(module.id, functionName, 'method', e.target.value)}
                            placeholder="GET, POST, PUT, DELETE"
                          />
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">
                        Full URL: {baseUrl}{config.endpoint}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
