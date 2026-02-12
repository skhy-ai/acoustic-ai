
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Save, RotateCcw, Upload, Settings } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface ParameterEditorProps {
  experiment: any;
}

const presetConfigurations = {
  "Urban Noise Detection": {
    sampling_rate: 48000,
    chunk_duration: 3.0,
    click_threshold: 0.6,
    window_size: 2048,
    pitch_shift_range: [-1, 1],
    noise_level: 0.05,
    volume_adjustment: 0,
    mfcc_coefficients: 13,
    learning_rate: 0.0005,
    batch_size: 64,
    classification_threshold: 0.8,
    clustering_method: "dbscan",
    directional_inference: "omnidirectional"
  },
  "Wildlife Monitoring": {
    sampling_rate: 44100,
    chunk_duration: 10.0,
    click_threshold: 0.9,
    window_size: 4096,
    pitch_shift_range: [-3, 3],
    noise_level: 0.02,
    volume_adjustment: 3,
    mfcc_coefficients: 20,
    learning_rate: 0.001,
    batch_size: 32,
    classification_threshold: 0.9,
    clustering_method: "hierarchical",
    directional_inference: "beamforming"
  },
  "Industrial Sound Analysis": {
    sampling_rate: 96000,
    chunk_duration: 2.0,
    click_threshold: 0.5,
    window_size: 1024,
    pitch_shift_range: [0, 0],
    noise_level: 0.1,
    volume_adjustment: -2,
    mfcc_coefficients: 16,
    learning_rate: 0.002,
    batch_size: 128,
    classification_threshold: 0.7,
    clustering_method: "kmeans",
    directional_inference: "multi_directional"
  },
  "Music Analysis": {
    sampling_rate: 44100,
    chunk_duration: 5.0,
    click_threshold: 0.7,
    window_size: 2048,
    pitch_shift_range: [-5, 5],
    noise_level: 0.01,
    volume_adjustment: 0,
    mfcc_coefficients: 25,
    learning_rate: 0.0008,
    batch_size: 48,
    classification_threshold: 0.85,
    clustering_method: "kmeans",
    directional_inference: "stereo_analysis"
  }
};

export function ParameterEditor({ experiment }: ParameterEditorProps) {
  const { toast } = useToast();
  const [parameters, setParameters] = useState({
    // M1: Data Acquisition
    sampling_rate: 44100,
    chunk_duration: 5.0,
    buffer_size: 1024,
    sensor_type: "mems",
    
    // M2: Preprocessing  
    click_threshold: 0.8,
    window_size: 2048,
    hop_length: 512,
    overlap_ratio: 0.5,
    
    // M3: Augmentation
    pitch_shift_range: [-2, 2],
    noise_level: 0.1,
    stretch_factor: [0.8, 1.2],
    amplitude_range: [0.7, 1.3],
    volume_adjustment: 0, // New: Volume in dB
    
    // M4: ML Processing
    mfcc_coefficients: 13,
    learning_rate: 0.001,
    batch_size: 32,
    epochs: 100,
    directional_inference: "omnidirectional", // New: Directional inference engine
    
    // M5: Applications
    classification_threshold: 0.7,
    clustering_method: "kmeans",
    anomaly_threshold: 0.9
  });

  const updateParameter = (key: string, value: any) => {
    setParameters(prev => ({ ...prev, [key]: value }));
  };

  const saveParameters = () => {
    toast({
      title: "Parameters Saved",
      description: "All module parameters have been saved successfully."
    });
  };

  const resetToDefaults = () => {
    setParameters({
      sampling_rate: 44100,
      chunk_duration: 5.0,
      buffer_size: 1024,
      sensor_type: "mems",
      click_threshold: 0.8,
      window_size: 2048,
      hop_length: 512,
      overlap_ratio: 0.5,
      pitch_shift_range: [-2, 2],
      noise_level: 0.1,
      stretch_factor: [0.8, 1.2],
      amplitude_range: [0.7, 1.3],
      volume_adjustment: 0,
      mfcc_coefficients: 13,
      learning_rate: 0.001,
      batch_size: 32,
      epochs: 100,
      directional_inference: "omnidirectional",
      classification_threshold: 0.7,
      clustering_method: "kmeans",
      anomaly_threshold: 0.9
    });
    toast({
      title: "Parameters Reset",
      description: "All parameters have been reset to default values."
    });
  };

  const loadPreset = (presetName: string) => {
    const presetConfig = presetConfigurations[presetName as keyof typeof presetConfigurations];
    if (presetConfig) {
      setParameters(prev => ({ ...prev, ...presetConfig }));
      toast({
        title: "Preset Loaded",
        description: `${presetName} parameter preset has been applied.`
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Parameter Editor</h2>
          <p className="text-gray-600">Configure module-specific parameters</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={resetToDefaults}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button onClick={saveParameters}>
            <Save className="h-4 w-4 mr-2" />
            Save Parameters
          </Button>
        </div>
      </div>

      {/* Preset Configurations */}
      <Card>
        <CardHeader>
          <CardTitle>Preset Configurations</CardTitle>
          <CardDescription>Load pre-configured parameter sets for common experiments</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.keys(presetConfigurations).map((preset) => (
              <Button 
                key={preset}
                variant="outline" 
                onClick={() => loadPreset(preset)}
                className="text-sm h-auto p-3 flex flex-col items-start"
              >
                <span className="font-medium">{preset}</span>
                <span className="text-xs text-gray-500 mt-1">
                  {preset === "Urban Noise Detection" && "High-frequency analysis"}
                  {preset === "Wildlife Monitoring" && "Long-duration recording"}
                  {preset === "Industrial Sound Analysis" && "High-precision detection"}
                  {preset === "Music Analysis" && "Tonal analysis optimized"}
                </span>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Parameter Tabs */}
      <Tabs defaultValue="m1" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="m1">M1: Data</TabsTrigger>
          <TabsTrigger value="m2">M2: Preprocess</TabsTrigger>
          <TabsTrigger value="m3">M3: Augment</TabsTrigger>
          <TabsTrigger value="m4">M4: ML</TabsTrigger>
          <TabsTrigger value="m5">M5: Apps</TabsTrigger>
        </TabsList>

        {/* M1: Data Acquisition Parameters */}
        <TabsContent value="m1">
          <Card>
            <CardHeader>
              <CardTitle>Data Acquisition Parameters</CardTitle>
              <CardDescription>Configure sensors and streaming settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="sampling_rate">Sampling Rate (Hz)</Label>
                  <Select value={parameters.sampling_rate.toString()} onValueChange={(v) => updateParameter("sampling_rate", parseInt(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="22050">22,050 Hz</SelectItem>
                      <SelectItem value="44100">44,100 Hz</SelectItem>
                      <SelectItem value="48000">48,000 Hz</SelectItem>
                      <SelectItem value="96000">96,000 Hz</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="chunk_duration">Chunk Duration (seconds)</Label>
                  <Input
                    id="chunk_duration"
                    type="number"
                    step="0.1"
                    value={parameters.chunk_duration}
                    onChange={(e) => updateParameter("chunk_duration", parseFloat(e.target.value))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="buffer_size">Buffer Size</Label>
                  <Select value={parameters.buffer_size.toString()} onValueChange={(v) => updateParameter("buffer_size", parseInt(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="512">512</SelectItem>
                      <SelectItem value="1024">1024</SelectItem>
                      <SelectItem value="2048">2048</SelectItem>
                      <SelectItem value="4096">4096</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sensor_type">Sensor Type</Label>
                  <Select value={parameters.sensor_type} onValueChange={(v) => updateParameter("sensor_type", v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mems">MEMS Microphone</SelectItem>
                      <SelectItem value="ultrasonic">Ultrasonic Sensor</SelectItem>
                      <SelectItem value="hydrophone">Hydrophone</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* M2: Preprocessing Parameters */}
        <TabsContent value="m2">
          <Card>
            <CardHeader>
              <CardTitle>Preprocessing Parameters</CardTitle>
              <CardDescription>Configure chunking and cleaning settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Click Detection Threshold: {parameters.click_threshold}</Label>
                  <Slider
                    value={[parameters.click_threshold]}
                    onValueChange={(v) => updateParameter("click_threshold", v[0])}
                    max={1}
                    min={0}
                    step={0.1}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="window_size">Window Size</Label>
                  <Select value={parameters.window_size.toString()} onValueChange={(v) => updateParameter("window_size", parseInt(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1024">1024</SelectItem>
                      <SelectItem value="2048">2048</SelectItem>
                      <SelectItem value="4096">4096</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hop_length">Hop Length</Label>
                  <Input
                    id="hop_length"
                    type="number"
                    value={parameters.hop_length}
                    onChange={(e) => updateParameter("hop_length", parseInt(e.target.value))}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Overlap Ratio: {parameters.overlap_ratio}</Label>
                  <Slider
                    value={[parameters.overlap_ratio]}
                    onValueChange={(v) => updateParameter("overlap_ratio", v[0])}
                    max={0.9}
                    min={0.1}
                    step={0.1}
                    className="w-full"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* M3: Augmentation Parameters */}
        <TabsContent value="m3">
          <Card>
            <CardHeader>
              <CardTitle>Data Augmentation Parameters</CardTitle>
              <CardDescription>Configure audio transformation settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Pitch Shift Range: [{parameters.pitch_shift_range[0]}, {parameters.pitch_shift_range[1]}] semitones</Label>
                  <div className="flex gap-4">
                    <Slider
                      value={parameters.pitch_shift_range}
                      onValueChange={(v) => updateParameter("pitch_shift_range", v)}
                      max={12}
                      min={-12}
                      step={1}
                      className="w-full"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Noise Level: {parameters.noise_level}</Label>
                  <Slider
                    value={[parameters.noise_level]}
                    onValueChange={(v) => updateParameter("noise_level", v[0])}
                    max={0.5}
                    min={0}
                    step={0.01}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Volume Adjustment: {parameters.volume_adjustment > 0 ? '+' : ''}{parameters.volume_adjustment} dB</Label>
                  <Slider
                    value={[parameters.volume_adjustment]}
                    onValueChange={(v) => updateParameter("volume_adjustment", v[0])}
                    max={20}
                    min={-20}
                    step={0.5}
                    className="w-full"
                  />
                  <div className="text-xs text-gray-500">
                    Positive values increase volume, negative values decrease volume
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Time Stretch Factor: [{parameters.stretch_factor[0]}, {parameters.stretch_factor[1]}]</Label>
                  <div className="flex gap-4">
                    <Slider
                      value={parameters.stretch_factor}
                      onValueChange={(v) => updateParameter("stretch_factor", v)}
                      max={2}
                      min={0.5}
                      step={0.1}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* M4: ML Processing Parameters */}
        <TabsContent value="m4">
          <Card>
            <CardHeader>
              <CardTitle>Machine Learning Parameters</CardTitle>
              <CardDescription>Configure feature extraction and training settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="mfcc_coefficients">MFCC Coefficients</Label>
                  <Input
                    id="mfcc_coefficients"
                    type="number"
                    value={parameters.mfcc_coefficients}
                    onChange={(e) => updateParameter("mfcc_coefficients", parseInt(e.target.value))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="learning_rate">Learning Rate</Label>
                  <Input
                    id="learning_rate"
                    type="number"
                    step="0.0001"
                    value={parameters.learning_rate}
                    onChange={(e) => updateParameter("learning_rate", parseFloat(e.target.value))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="batch_size">Batch Size</Label>
                  <Select value={parameters.batch_size.toString()} onValueChange={(v) => updateParameter("batch_size", parseInt(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="16">16</SelectItem>
                      <SelectItem value="32">32</SelectItem>
                      <SelectItem value="64">64</SelectItem>
                      <SelectItem value="128">128</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="epochs">Training Epochs</Label>
                  <Input
                    id="epochs"
                    type="number"
                    value={parameters.epochs}
                    onChange={(e) => updateParameter("epochs", parseInt(e.target.value))}
                  />
                </div>

                <div className="space-y-2 col-span-2">
                  <Label htmlFor="directional_inference">Directional Inference Engine</Label>
                  <Select value={parameters.directional_inference} onValueChange={(v) => updateParameter("directional_inference", v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="omnidirectional">Omnidirectional (360° coverage)</SelectItem>
                      <SelectItem value="beamforming">Beamforming (focused direction)</SelectItem>
                      <SelectItem value="multi_directional">Multi-directional (multiple zones)</SelectItem>
                      <SelectItem value="stereo_analysis">Stereo Analysis (L/R separation)</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="text-xs text-gray-500 mt-1">
                    {parameters.directional_inference === "omnidirectional" && "Captures sound from all directions equally"}
                    {parameters.directional_inference === "beamforming" && "Focuses on specific direction, reduces noise from other directions"}
                    {parameters.directional_inference === "multi_directional" && "Analyzes multiple directional zones simultaneously"}
                    {parameters.directional_inference === "stereo_analysis" && "Separates left and right channel analysis for spatial processing"}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* M5: Applications Parameters */}
        <TabsContent value="m5">
          <Card>
            <CardHeader>
              <CardTitle>Application Parameters</CardTitle>
              <CardDescription>Configure inference and analysis settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Classification Threshold: {parameters.classification_threshold}</Label>
                  <Slider
                    value={[parameters.classification_threshold]}
                    onValueChange={(v) => updateParameter("classification_threshold", v[0])}
                    max={1}
                    min={0}
                    step={0.1}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="clustering_method">Clustering Method</Label>
                  <Select value={parameters.clustering_method} onValueChange={(v) => updateParameter("clustering_method", v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="kmeans">K-Means</SelectItem>
                      <SelectItem value="dbscan">DBSCAN</SelectItem>
                      <SelectItem value="hierarchical">Hierarchical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Anomaly Threshold: {parameters.anomaly_threshold}</Label>
                  <Slider
                    value={[parameters.anomaly_threshold]}
                    onValueChange={(v) => updateParameter("anomaly_threshold", v[0])}
                    max={1}
                    min={0}
                    step={0.1}
                    className="w-full"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
