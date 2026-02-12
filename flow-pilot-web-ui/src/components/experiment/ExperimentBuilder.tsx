import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Mic, 
  Waves, 
  Settings, 
  Brain, 
  Target, 
  ArrowDown,
  ArrowRight,
  Play,
  Save,
  Workflow,
  Plus,
  Trash2
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { experimentService, type Experiment } from "@/services/experimentService";

interface Module {
  id: string;
  name: string;
  icon: string; // Changed to string to store icon name
  enabled: boolean;
  submodules: {
    id: string;
    name: string;
    enabled: boolean;
    description: string;
  }[];
}

interface ExperimentBuilderProps {
  onExperimentChange: (experiment: any) => void;
}

// Icon mapping object
const iconMap = {
  Mic,
  Waves,
  Settings,
  Brain,
  Target
};

export function ExperimentBuilder({ onExperimentChange }: ExperimentBuilderProps) {
  const { toast } = useToast();
  const [experimentName, setExperimentName] = useState("Custom Acoustic Experiment");
  const [experimentDescription, setExperimentDescription] = useState("");
  const [savedExperiments, setSavedExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(false);

  const [modules, setModules] = useState<Module[]>([
    {
      id: "m1",
      name: "M1: Data Acquisition",
      icon: "Mic", // Changed to string
      enabled: true,
      submodules: [
        { id: "sensors", name: "Acoustic Sensors", enabled: true, description: "MEMS, ultrasonic, hydrophone" },
        { id: "streaming", name: "Streaming Services", enabled: false, description: "YouTube, Spotify APIs" },
        { id: "beamforming", name: "Beamforming", enabled: false, description: "MVDR, MUSIC algorithms" },
        { id: "multi_device", name: "Multi-Device", enabled: false, description: "Concurrent capture" }
      ]
    },
    {
      id: "m2", 
      name: "M2: Preprocessing",
      icon: "Waves", // Changed to string
      enabled: true,
      submodules: [
        { id: "click_detection", name: "Click Detection", enabled: true, description: "Transient removal" },
        { id: "sliding_window", name: "Sliding Windows", enabled: true, description: "Overlapping chunks" },
        { id: "sound_separation", name: "Sound Separation", enabled: false, description: "Source separation" }
      ]
    },
    {
      id: "m3",
      name: "M3: Data Augmentation", 
      icon: "Settings", // Changed to string
      enabled: true,
      submodules: [
        { id: "amplitude", name: "Amplitude Adjust", enabled: false, description: "Increase/decrease dB" },
        { id: "reversal", name: "Sound Reversal", enabled: false, description: "Time-reverse audio" },
        { id: "pitch_shift", name: "Pitch Shifting", enabled: true, description: "Librosa pitch shift" },
        { id: "noise_injection", name: "Noise Injection", enabled: true, description: "Gaussian noise" },
        { id: "time_stretch", name: "Time Stretching", enabled: false, description: "Tempo modification" }
      ]
    },
    {
      id: "m4",
      name: "M4: ML Processing",
      icon: "Brain", // Changed to string
      enabled: true,
      submodules: [
        { id: "feature_extraction", name: "Feature Extraction", enabled: true, description: "MFCCs, spectral features" },
        { id: "training", name: "Neural Network Training", enabled: true, description: "PyTorch CNN" },
        { id: "vae", name: "Variational Autoencoder", enabled: false, description: "Unsupervised learning" },
        { id: "directional", name: "Directional Inference", enabled: false, description: "TDOA-based DOA" }
      ]
    },
    {
      id: "m5",
      name: "M5: Applications",
      icon: "Target", // Changed to string
      enabled: true,
      submodules: [
        { id: "classification", name: "Sound Classification", enabled: true, description: "Inference pipeline" },
        { id: "scene_analysis", name: "Scene Analysis", enabled: false, description: "Clustering algorithms" },
        { id: "mapping", name: "Mapping & Inference", enabled: false, description: "Geolocation via DOA" },
        { id: "anomaly", name: "Anomaly Detection", enabled: false, description: "VAE-based detection" }
      ]
    }
  ]);

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    try {
      const experiments = await experimentService.getExperiments();
      setSavedExperiments(experiments);
    } catch (error) {
      console.error('Error loading experiments:', error);
    }
  };

  const toggleModule = (moduleId: string) => {
    setModules(prev => prev.map(module => 
      module.id === moduleId 
        ? { ...module, enabled: !module.enabled }
        : module
    ));
  };

  const toggleSubmodule = (moduleId: string, submoduleId: string) => {
    setModules(prev => prev.map(module =>
      module.id === moduleId
        ? {
            ...module,
            submodules: module.submodules.map(sub =>
              sub.id === submoduleId
                ? { ...sub, enabled: !sub.enabled }
                : sub
            )
          }
        : module
    ));
  };

  const saveExperiment = async () => {
    try {
      setLoading(true);
      const experiment = await experimentService.createExperiment({
        name: experimentName,
        description: experimentDescription,
        configuration: {
          modules: modules.filter(m => m.enabled)
        }
      });
      
      onExperimentChange(experiment);
      await loadExperiments();
      
      toast({
        title: "Experiment Saved",
        description: "Workflow configuration has been saved successfully."
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save experiment. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadExperiment = async (experiment: Experiment) => {
    try {
      if (experiment.configuration?.modules) {
        setModules(experiment.configuration.modules);
      }
      setExperimentName(experiment.name);
      setExperimentDescription(experiment.description || "");
      onExperimentChange(experiment);
      
      toast({
        title: "Experiment Loaded",
        description: `${experiment.name} configuration has been applied.`
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load experiment.",
        variant: "destructive"
      });
    }
  };

  const deleteExperiment = async (id: string) => {
    try {
      await experimentService.deleteExperiment(id);
      await loadExperiments();
      
      toast({
        title: "Experiment Deleted",
        description: "Experiment has been removed successfully."
      });
    } catch (error) {
      toast({
        title: "Error", 
        description: "Failed to delete experiment.",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Experiment Builder</h2>
          <p className="text-gray-600">Design your acoustic AI workflow pipeline</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => loadExperiments()}>
            Refresh
          </Button>
          <Button onClick={saveExperiment} disabled={loading} className="flex items-center gap-2">
            <Save className="h-4 w-4" />
            {loading ? "Saving..." : "Save Experiment"}
          </Button>
        </div>
      </div>

      {/* Experiment Details */}
      <Card>
        <CardHeader>
          <CardTitle>Experiment Details</CardTitle>
          <CardDescription>Configure experiment name and description</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="experimentName">Experiment Name</Label>
            <Input
              id="experimentName"
              value={experimentName}
              onChange={(e) => setExperimentName(e.target.value)}
              placeholder="Enter experiment name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="experimentDescription">Description (Optional)</Label>
            <Input
              id="experimentDescription"
              value={experimentDescription}
              onChange={(e) => setExperimentDescription(e.target.value)}
              placeholder="Describe your experiment"
            />
          </div>
        </CardContent>
      </Card>

      {/* Saved Experiments */}
      {savedExperiments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Saved Experiments</CardTitle>
            <CardDescription>Load or manage your saved experiments</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savedExperiments.map((experiment) => (
                <div key={experiment.id} className="p-4 border rounded-lg space-y-3">
                  <div>
                    <h3 className="font-semibold">{experiment.name}</h3>
                    <p className="text-sm text-gray-500">{experiment.description}</p>
                    <p className="text-xs text-gray-400">
                      Created: {new Date(experiment.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => loadExperiment(experiment)}
                      className="flex-1"
                    >
                      Load
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => deleteExperiment(experiment.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Workflow Pipeline Visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Workflow className="h-5 w-5" />
            Workflow Pipeline
          </CardTitle>
          <CardDescription>
            Drag and drop modules to design your acoustic AI pipeline
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {modules.map((module, index) => {
              const IconComponent = iconMap[module.icon as keyof typeof iconMap] || Settings;
              return (
                <div key={module.id} className="space-y-3">
                  <div className="flex items-center justify-between p-4 border rounded-lg bg-white">
                    <div className="flex items-center gap-3">
                      <IconComponent className="h-6 w-6 text-blue-600" />
                      <div>
                        <h3 className="font-semibold">{module.name}</h3>
                        <p className="text-sm text-gray-500">
                          {module.submodules.filter(s => s.enabled).length} of {module.submodules.length} submodules enabled
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={module.enabled ? "default" : "secondary"}>
                        {module.enabled ? "Enabled" : "Disabled"}
                      </Badge>
                      <Switch
                        checked={module.enabled}
                        onCheckedChange={() => toggleModule(module.id)}
                      />
                    </div>
                  </div>

                  {/* Submodules */}
                  {module.enabled && (
                    <div className="ml-8 space-y-2">
                      {module.submodules.map((submodule) => (
                        <div key={submodule.id} className="flex items-center justify-between p-3 border rounded bg-gray-50">
                          <div>
                            <h4 className="font-medium text-sm">{submodule.name}</h4>
                            <p className="text-xs text-gray-500">{submodule.description}</p>
                          </div>
                          <Switch
                            checked={submodule.enabled}
                            onCheckedChange={() => toggleSubmodule(module.id, submodule.id)}
                          />
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Arrow between modules */}
                  {index < modules.length - 1 && module.enabled && (
                    <div className="flex justify-center">
                      <ArrowDown className="h-6 w-6 text-gray-400" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Deployment Options */}
      <Card>
        <CardHeader>
          <CardTitle>Deployment Configuration</CardTitle>
          <CardDescription>
            Select where this experiment will be executed
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg text-center hover:bg-gray-50 cursor-pointer">
              <h3 className="font-semibold">D1: Cloud</h3>
              <p className="text-sm text-gray-500 mt-1">Scalable batch experiments</p>
            </div>
            <div className="p-4 border rounded-lg text-center hover:bg-gray-50 cursor-pointer">
              <h3 className="font-semibold">D2: Edge</h3>
              <p className="text-sm text-gray-500 mt-1">On-device IoT deployment</p>
            </div>
            <div className="p-4 border rounded-lg text-center hover:bg-gray-50 cursor-pointer">
              <h3 className="font-semibold">D3: On-Prem</h3>
              <p className="text-sm text-gray-500 mt-1">Secure internal usage</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
