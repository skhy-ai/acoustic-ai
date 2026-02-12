
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Activity, 
  FileText, 
  AlertCircle, 
  CheckCircle,
  Clock,
  Database,
  Cpu,
  PlayCircle,
  PauseCircle
} from "lucide-react";

interface LogEntry {
  id: string;
  timestamp: string;
  level: "info" | "warning" | "error" | "success";
  module: string;
  message: string;
}

export function LiveMonitor() {
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState("M1: Acquiring sensor data...");
  const [progress, setProgress] = useState(25);
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: "1",
      timestamp: "2024-05-29 10:30:15",
      level: "info",
      module: "M1",
      message: "Initializing MEMS sensors with 44.1kHz sampling rate"
    },
    {
      id: "2", 
      timestamp: "2024-05-29 10:30:16",
      level: "success",
      module: "M1",
      message: "Successfully acquired 1,247 audio chunks (5s each)"
    },
    {
      id: "3",
      timestamp: "2024-05-29 10:30:45",
      level: "info",
      module: "M2",
      message: "Starting click detection with threshold 0.8"
    },
    {
      id: "4",
      timestamp: "2024-05-29 10:31:02",
      level: "warning",
      module: "M2",
      message: "Detected 23 transient clicks, removing from dataset"
    },
    {
      id: "5",
      timestamp: "2024-05-29 10:31:15",
      level: "info",
      module: "M3",
      message: "Applying pitch shifting (-2 to +2 semitones)"
    }
  ]);

  const [stats, setStats] = useState({
    filesProcessed: 1247,
    chunkedFiles: 1224,
    augmentedSamples: 3672,
    currentStage: "M3: Data Augmentation",
    timeElapsed: "00:02:15",
    estimatedRemaining: "00:03:45"
  });

  // Simulate real-time updates
  useEffect(() => {
    if (isRunning) {
      const interval = setInterval(() => {
        // Add new log entry
        const newLog: LogEntry = {
          id: Date.now().toString(),
          timestamp: new Date().toLocaleString(),
          level: Math.random() > 0.8 ? "warning" : "info",
          module: `M${Math.floor(Math.random() * 5) + 1}`,
          message: getRandomLogMessage()
        };
        
        setLogs(prev => [newLog, ...prev.slice(0, 19)]); // Keep last 20 logs
        
        // Update progress
        setProgress(prev => Math.min(prev + Math.random() * 5, 100));
        
        // Update stats
        setStats(prev => ({
          ...prev,
          filesProcessed: prev.filesProcessed + Math.floor(Math.random() * 10),
          augmentedSamples: prev.augmentedSamples + Math.floor(Math.random() * 50)
        }));
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isRunning]);

  const getRandomLogMessage = () => {
    const messages = [
      "Processing audio chunk batch #342",
      "Applying Gaussian noise injection (level: 0.1)",
      "Feature extraction: computing MFCCs",
      "Neural network training: epoch 15/100",
      "Validating augmented dataset integrity",
      "Saving processed files to /experiments/exp_001/",
      "Click detection completed for current batch",
      "Time stretching applied (factor: 0.9-1.1)"
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  };

  const getLogIcon = (level: string) => {
    switch (level) {
      case "success": return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "warning": return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case "error": return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <FileText className="h-4 w-4 text-blue-500" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "success": return "text-green-600";
      case "warning": return "text-yellow-600";
      case "error": return "text-red-600";
      default: return "text-blue-600";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Live Monitor</h2>
          <p className="text-gray-600">Real-time experiment execution and logging</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant={isRunning ? "outline" : "default"}
            onClick={() => setIsRunning(!isRunning)}
            className="flex items-center gap-2"
          >
            {isRunning ? (
              <>
                <PauseCircle className="h-4 w-4" />
                Pause
              </>
            ) : (
              <>
                <PlayCircle className="h-4 w-4" />
                Start Monitoring
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Current Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Files Processed</p>
                <p className="text-2xl font-bold">{stats.filesProcessed.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Augmented Samples</p>
                <p className="text-2xl font-bold">{stats.augmentedSamples.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-sm font-medium">Time Elapsed</p>
                <p className="text-2xl font-bold">{stats.timeElapsed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-sm font-medium">ETA Remaining</p>
                <p className="text-2xl font-bold">{stats.estimatedRemaining}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Progress & Current Step */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Experiment Progress
          </CardTitle>
          <CardDescription>Current pipeline execution status</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">{currentStep}</span>
              <span className="text-sm text-gray-500">{Math.round(progress)}% complete</span>
            </div>
            <Progress value={progress} className="w-full" />
          </div>
          
          <div className="flex items-center gap-2">
            <Badge variant={isRunning ? "default" : "secondary"}>
              {isRunning ? "Running" : "Paused"}
            </Badge>
            <Badge variant="outline">{stats.currentStage}</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Live Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Live Logs
          </CardTitle>
          <CardDescription>Real-time logging from all modules</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96 w-full">
            <div className="space-y-2">
              {logs.map((log) => (
                <div key={log.id} className="flex items-start gap-3 p-3 border rounded-lg text-sm">
                  {getLogIcon(log.level)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-gray-500">{log.timestamp}</span>
                      <Badge variant="outline" className="text-xs">{log.module}</Badge>
                      <span className={`text-xs font-semibold ${getLevelColor(log.level)}`}>
                        {log.level.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-700">{log.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
