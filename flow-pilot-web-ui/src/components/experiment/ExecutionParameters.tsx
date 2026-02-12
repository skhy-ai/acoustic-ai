
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Mic,
  Globe,
  HardDrive,
  CheckCircle,
  XCircle,
  Clock,
  Wifi,
  Radio
} from "lucide-react";
import { getDevices, checkHealth } from "@/services/dataAcquisitionService";

interface ExecutionParametersProps {
  onParametersChange: (params: any) => void;
}

export function ExecutionParameters({ onParametersChange }: ExecutionParametersProps) {
  const [acousticSensor, setAcousticSensor] = useState("");
  const [streamingService, setStreamingService] = useState("");
  const [concurrentCapture, setConcurrentCapture] = useState(false);
  const [externalDataset, setExternalDataset] = useState("");
  const [customDatasetUrl, setCustomDatasetUrl] = useState("");
  const [backendOnline, setBackendOnline] = useState(false);

  // Orange Pi UDP config
  const [orangePiHost, setOrangePiHost] = useState("0.0.0.0");
  const [orangePiPort, setOrangePiPort] = useState("5000");

  const [serviceStatus, setServiceStatus] = useState({
    sensors: "idle",
    streaming: "idle",
    dataset: "idle",
    storage: "idle"
  });

  // Check backend health on mount
  useEffect(() => {
    checkHealth().then(setBackendOnline);
  }, []);

  const acousticSensors = [
    { id: "hydrophone", name: "Hydrophone (USB)", status: "available", icon: Mic },
    { id: "7mems", name: "7-MEMS (HISPEED Board)", status: "available", icon: Radio },
    { id: "16mems", name: "16-MEMS (Orange Pi)", status: "available", icon: Wifi },
    { id: "bluetooth", name: "Bluetooth Microphone", status: "available", icon: Mic },
    { id: "contact_mic", name: "Contact Microphone", status: "available", icon: Mic },
  ];

  const streamingServices = [
    { id: "youtube", name: "YouTube Audio", status: "connected" },
    { id: "soundcloud", name: "SoundCloud", status: "connected" },
    { id: "custom_stream", name: "Custom Stream", status: "available" },
  ];

  const externalDatasets = [
    { id: "urbansound8k", name: "UrbanSound8K", size: "6.2 GB", status: "available" },
    { id: "esc50", name: "ESC-50", size: "600 MB", status: "available" },
    { id: "freesound", name: "FreeSound", size: "Variable", status: "api_required" },
    { id: "custom", name: "Custom Dataset", size: "Variable", status: "available" },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "available":
      case "connected":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
      case "maintenance":
      case "disconnected":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "api_required":
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      available: "default",
      connected: "default",
      error: "destructive",
      maintenance: "destructive",
      disconnected: "destructive",
      api_required: "secondary",
      idle: "outline"
    };
    return variants[status] || "outline";
  };

  const handleParameterUpdate = () => {
    const params = {
      acousticSensor,
      streamingService,
      concurrentCapture,
      externalDataset,
      storageLocation: "local",  // Always local
      customDatasetUrl: externalDataset === "custom" ? customDatasetUrl : "",
      orangePiConfig: acousticSensor === "16mems" ? {
        host: orangePiHost,
        port: parseInt(orangePiPort),
      } : undefined,
    };
    onParametersChange(params);
  };

  const testConnection = (service: string) => {
    setServiceStatus(prev => ({ ...prev, [service]: "testing" }));
    // Test against the local backend
    checkHealth().then(ok => {
      setServiceStatus(prev => ({
        ...prev,
        [service]: ok ? "connected" : "error"
      }));
    });
  };

  return (
    <div className="space-y-6">
      {/* Backend Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            {backendOnline
              ? <CheckCircle className="h-5 w-5 text-green-500" />
              : <XCircle className="h-5 w-5 text-red-500" />}
            <span>Python Backend: {backendOnline ? "Online" : "Offline"}</span>
            <Badge variant={backendOnline ? "default" : "destructive"}>
              {backendOnline ? "Connected" : "Disconnected"}
            </Badge>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Storage: <strong>Local (SQLite)</strong> — All data stays on your machine.
          </p>
        </CardContent>
      </Card>

      {/* Acoustic Sensors */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5" />
            Acoustic Sensors
          </CardTitle>
          <CardDescription>Select the acoustic sensor for data acquisition</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Select value={acousticSensor} onValueChange={setAcousticSensor}>
              <SelectTrigger>
                <SelectValue placeholder="Select acoustic sensor" />
              </SelectTrigger>
              <SelectContent>
                {acousticSensors.map((sensor) => (
                  <SelectItem key={sensor.id} value={sensor.id}>
                    <div className="flex items-center justify-between w-full">
                      <span>{sensor.name}</span>
                      <Badge variant={getStatusBadge(sensor.status) as "default" | "destructive" | "outline" | "secondary"} className="ml-2">
                        {sensor.status}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Orange Pi UDP Configuration */}
            {acousticSensor === "16mems" && (
              <div className="space-y-2 p-3 border rounded-lg bg-gray-50">
                <Label className="text-sm font-medium">Orange Pi UDP Configuration</Label>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs">Host IP</Label>
                    <Input value={orangePiHost} onChange={e => setOrangePiHost(e.target.value)} placeholder="0.0.0.0" />
                  </div>
                  <div>
                    <Label className="text-xs">Port</Label>
                    <Input value={orangePiPort} onChange={e => setOrangePiPort(e.target.value)} placeholder="5000" />
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <Switch
                id="concurrent"
                checked={concurrentCapture}
                onCheckedChange={setConcurrentCapture}
              />
              <Label htmlFor="concurrent">Enable concurrent multi-device capture</Label>
            </div>

            {acousticSensor && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => testConnection("sensors")}
              >
                {getStatusIcon(serviceStatus.sensors)}
                Test Connection
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Streaming Services */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Streaming Services
          </CardTitle>
          <CardDescription>Configure audio streaming sources</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Select value={streamingService} onValueChange={setStreamingService}>
              <SelectTrigger>
                <SelectValue placeholder="Select streaming service" />
              </SelectTrigger>
              <SelectContent>
                {streamingServices.map((service) => (
                  <SelectItem key={service.id} value={service.id}>
                    <div className="flex items-center justify-between w-full">
                      <span>{service.name}</span>
                      <Badge variant={getStatusBadge(service.status) as "default" | "destructive" | "outline" | "secondary"} className="ml-2">
                        {service.status}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {streamingService && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => testConnection("streaming")}
              >
                {getStatusIcon(serviceStatus.streaming)}
                Test API Connection
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* External Datasets */}
      <Card>
        <CardHeader>
          <CardTitle>External Datasets</CardTitle>
          <CardDescription>Select external dataset for training/evaluation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Select value={externalDataset} onValueChange={setExternalDataset}>
              <SelectTrigger>
                <SelectValue placeholder="Select external dataset" />
              </SelectTrigger>
              <SelectContent>
                {externalDatasets.map((dataset) => (
                  <SelectItem key={dataset.id} value={dataset.id}>
                    <div className="flex items-center justify-between w-full">
                      <div>
                        <div>{dataset.name}</div>
                        <div className="text-xs text-gray-500">{dataset.size}</div>
                      </div>
                      <Badge variant={getStatusBadge(dataset.status) as "default" | "destructive" | "outline" | "secondary"} className="ml-2">
                        {dataset.status}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {externalDataset === "custom" && (
              <Input
                placeholder="Enter custom dataset URL or local path"
                value={customDatasetUrl}
                onChange={(e) => setCustomDatasetUrl(e.target.value)}
              />
            )}

            {externalDataset && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => testConnection("dataset")}
              >
                {getStatusIcon(serviceStatus.dataset)}
                Verify Dataset Access
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleParameterUpdate} className="w-full">
        Apply Parameters
      </Button>
    </div>
  );
}
