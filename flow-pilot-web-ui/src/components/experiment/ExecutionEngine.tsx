import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Play, 
  Square, 
  RotateCcw, 
  CheckCircle, 
  AlertTriangle,
  Clock,
  Cpu,
  HardDrive,
  Activity,
  Settings
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { experimentService, type ExperimentExecution } from "@/services/experimentService";
import { ExecutionParameters } from "./ExecutionParameters";
import { AIModuleConfig } from "./AIModuleConfig";

interface ExecutionEngineProps {
  experiment: any;
}

export function ExecutionEngine({ experiment }: ExecutionEngineProps) {
  const { toast } = useToast();
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [executionStatus, setExecutionStatus] = useState("ready");
  const [progress, setProgress] = useState(0);
  const [currentModule, setCurrentModule] = useState("");
  const [currentExecution, setCurrentExecution] = useState<ExperimentExecution | null>(null);
  const [executionParams, setExecutionParams] = useState<any>(null);
  const [moduleConfig, setModuleConfig] = useState<any>(null);

  const [systemMetrics, setSystemMetrics] = useState({
    cpuUsage: 45,
    memoryUsage: 68,
    diskUsage: 23,
    gpuUsage: 12
  });

  const [executionSteps] = useState([
    { id: "validate", name: "Validate Configuration", status: "completed", duration: "2s" },
    { id: "init", name: "Initialize Environment", status: "completed", duration: "5s" },
    { id: "m1", name: "M1: Data Acquisition", status: "running", duration: "45s" },
    { id: "m2", name: "M2: Preprocessing", status: "pending", duration: "~2m" },
    { id: "m3", name: "M3: Data Augmentation", status: "pending", duration: "~5m" },
    { id: "m4", name: "M4: ML Processing", status: "pending", duration: "~15m" },
    { id: "m5", name: "M5: Applications", status: "pending", duration: "~3m" }
  ]);

  const startExecution = async () => {
    if (!experiment) {
      toast({
        title: "No Experiment Selected",
        description: "Please configure an experiment first in the Experiment Builder.",
        variant: "destructive"
      });
      return;
    }

    if (!executionParams) {
      toast({
        title: "Missing Parameters",
        description: "Please configure execution parameters first.",
        variant: "destructive"
      });
      return;
    }

    if (!moduleConfig) {
      toast({
        title: "Missing Module Configuration",
        description: "Please configure AI module endpoints first.",
        variant: "destructive"
      });
      return;
    }

    try {
      const execution = await experimentService.createExecution(experiment.id);
      setCurrentExecution(execution);
      
      await experimentService.updateExecution(execution.id, {
        status: 'running',
        started_at: new Date().toISOString(),
        current_module: 'M1: Data Acquisition'
      });

      setIsRunning(true);
      setExecutionStatus("running");
      setCurrentModule("M1: Data Acquisition");
      
      toast({
        title: "Experiment Started",
        description: `Acoustic AI pipeline execution has begun with configured modules.`
      });

      const interval = setInterval(async () => {
        setProgress(prev => {
          const newProgress = prev + 2;
          
          if (currentExecution) {
            experimentService.updateExecution(currentExecution.id, {
              progress: newProgress
            }).catch(console.error);
          }
          
          if (newProgress >= 100) {
            clearInterval(interval);
            setIsRunning(false);
            setExecutionStatus("completed");
            
            if (currentExecution) {
              experimentService.updateExecution(currentExecution.id, {
                status: 'completed',
                completed_at: new Date().toISOString(),
                progress: 100
              }).catch(console.error);
            }
            
            toast({
              title: "Experiment Completed",
              description: "All modules have been executed successfully."
            });
            return 100;
          }
          return newProgress;
        });
      }, 1000);
    } catch (error) {
      toast({
        title: "Execution Error",
        description: "Failed to start experiment execution.",
        variant: "destructive"
      });
    }
  };

  const stopExecution = async () => {
    setIsRunning(false);
    setExecutionStatus("stopped");
    setCurrentModule("");
    
    if (currentExecution) {
      await experimentService.updateExecution(currentExecution.id, {
        status: 'stopped',
        completed_at: new Date().toISOString()
      });
    }
    
    toast({
      title: "Execution Stopped",
      description: "Experiment execution has been terminated."
    });
  };

  const resetExecution = () => {
    setIsRunning(false);
    setIsPaused(false);
    setExecutionStatus("ready");
    setProgress(0);
    setCurrentModule("");
    setCurrentExecution(null);
    
    toast({
      title: "Execution Reset",
      description: "Ready to start a new experiment."
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "text-green-600";
      case "running": return "text-blue-600";
      case "error": return "text-red-600";
      case "pending": return "text-gray-400";
      default: return "text-gray-600";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "running": return <Activity className="h-4 w-4 text-blue-500 animate-spin" />;
      case "error": return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Execution Engine</h2>
          <p className="text-gray-600">Run and monitor acoustic AI experiments</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={resetExecution}
            disabled={isRunning}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          {isRunning ? (
            <Button 
              variant="destructive" 
              onClick={stopExecution}
            >
              <Square className="h-4 w-4 mr-2" />
              Stop
            </Button>
          ) : (
            <Button onClick={startExecution}>
              <Play className="h-4 w-4 mr-2" />
              Start Execution
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="config" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="parameters">Parameters</TabsTrigger>
          <TabsTrigger value="modules">AI Modules</TabsTrigger>
          <TabsTrigger value="monitor">Monitor</TabsTrigger>
        </TabsList>

        <TabsContent value="config">
          {experiment && (
            <Card>
              <CardHeader>
                <CardTitle>Experiment Configuration</CardTitle>
                <CardDescription>Current experiment setup</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm font-medium">Experiment Name</p>
                    <p className="text-sm text-gray-600">{experiment.name}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Modules Enabled</p>
                    <p className="text-sm text-gray-600">{experiment.modules?.length || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Created</p>
                    <p className="text-sm text-gray-600">
                      {experiment.created ? new Date(experiment.created).toLocaleDateString() : "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Estimated Duration</p>
                    <p className="text-sm text-gray-600">~25 minutes</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="parameters">
          <ExecutionParameters onParametersChange={setExecutionParams} />
        </TabsContent>

        <TabsContent value="modules">
          <AIModuleConfig onConfigChange={setModuleConfig} />
        </TabsContent>

        <TabsContent value="monitor">
          {/* Execution Status */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Execution Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Overall Progress</span>
                  <Badge variant={isRunning ? "default" : "secondary"}>
                    {executionStatus.charAt(0).toUpperCase() + executionStatus.slice(1)}
                  </Badge>
                </div>
                
                <Progress value={progress} className="w-full" />
                
                <div className="text-sm text-gray-600">
                  {isRunning && currentModule && (
                    <p>Currently executing: <span className="font-medium">{currentModule}</span></p>
                  )}
                  <p>{Math.round(progress)}% complete</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  System Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>CPU Usage</span>
                    <span>{systemMetrics.cpuUsage}%</span>
                  </div>
                  <Progress value={systemMetrics.cpuUsage} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Memory Usage</span>
                    <span>{systemMetrics.memoryUsage}%</span>
                  </div>
                  <Progress value={systemMetrics.memoryUsage} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Disk I/O</span>
                    <span>{systemMetrics.diskUsage}%</span>
                  </div>
                  <Progress value={systemMetrics.diskUsage} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Execution Pipeline */}
          <Card>
            <CardHeader>
              <CardTitle>Execution Pipeline</CardTitle>
              <CardDescription>Step-by-step progress through the acoustic AI modules</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {executionSteps.map((step, index) => (
                  <div key={step.id} className="flex items-center gap-4 p-3 border rounded-lg">
                    {getStatusIcon(step.status)}
                    <div className="flex-1">
                      <h3 className={`font-medium ${getStatusColor(step.status)}`}>
                        {step.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {step.status === "completed" ? `Completed in ${step.duration}` : 
                         step.status === "running" ? "In progress..." :
                         `Estimated: ${step.duration}`}
                      </p>
                    </div>
                    <Badge variant={
                      step.status === "completed" ? "default" :
                      step.status === "running" ? "default" :
                      "secondary"
                    }>
                      {step.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Alerts and Notifications */}
          {executionStatus === "error" && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Execution Error</AlertTitle>
              <AlertDescription>
                An error occurred during experiment execution. Check the logs for more details.
              </AlertDescription>
            </Alert>
          )}

          {executionStatus === "completed" && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Execution Completed</AlertTitle>
              <AlertDescription>
                Your acoustic AI experiment has completed successfully. Results are available in the Data Viewer.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
