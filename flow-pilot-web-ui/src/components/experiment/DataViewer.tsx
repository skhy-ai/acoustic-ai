import { useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { 
  Download, 
  FileAudio, 
  BarChart3, 
  Eye,
  Activity,
  Sparkles,
  Play,
  Pause
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter } from "recharts";
import { ExperimentSelector } from "./ExperimentSelector";
import { useToast } from "@/hooks/use-toast";
import type { Experiment } from "@/services/experimentService";

// Mock data for visualizations
const waveformData = Array.from({ length: 100 }, (_, i) => ({
  time: i * 0.01,
  amplitude: Math.sin(i * 0.1) * 0.8 + Math.random() * 0.2
}));

const spectrogramData = Array.from({ length: 50 }, (_, i) => ({
  frequency: i * 100,
  magnitude: Math.random() * 100
}));

const mfccData = Array.from({ length: 13 }, (_, i) => ({
  coefficient: i + 1,
  value: Math.random() * 10 - 5
}));

const embeddingData = Array.from({ length: 100 }, (_, i) => ({
  x: Math.random() * 100 - 50,
  y: Math.random() * 100 - 50,
  cluster: Math.floor(Math.random() * 4)
}));

export function DataViewer() {
  const { toast } = useToast();
  const [selectedStage, setSelectedStage] = useState("raw");
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const processingStages = [
    { id: "raw", name: "Raw Audio", count: 1247, size: "2.3 GB" },
    { id: "chunked", name: "Chunked Files", count: 1224, size: "2.1 GB" },
    { id: "cleaned", name: "Cleaned Audio", count: 1201, size: "2.0 GB" },
    { id: "augmented", name: "Augmented Dataset", count: 3603, size: "6.2 GB" },
    { id: "features", name: "Extracted Features", count: 3603, size: "450 MB" },
    { id: "models", name: "Trained Models", count: 3, size: "125 MB" }
  ];

  const downloadFile = (stage: string, type: string) => {
    if (!selectedExperiment) {
      toast({
        title: "No Experiment Selected",
        description: "Please select an experiment first.",
        variant: "destructive"
      });
      return;
    }
    
    console.log(`Downloading ${type} from ${stage} stage for experiment ${selectedExperiment.name}`);
    toast({
      title: "Download Started",
      description: `Downloading ${type} files from ${stage} stage.`
    });
  };

  const downloadAllResults = () => {
    if (!selectedExperiment) {
      toast({
        title: "No Experiment Selected",
        description: "Please select an experiment first.",
        variant: "destructive"
      });
      return;
    }
    
    toast({
      title: "Download Started",
      description: `Downloading all results for experiment: ${selectedExperiment.name}`
    });
  };

  const toggleAudioPlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Data & Results Viewer</h2>
          <p className="text-gray-600">Explore processed audio data and visualizations</p>
        </div>
        <Button 
          className="flex items-center gap-2"
          onClick={downloadAllResults}
          disabled={!selectedExperiment}
        >
          <Download className="h-4 w-4" />
          Export All Results
        </Button>
      </div>

      {/* Experiment Selection */}
      <ExperimentSelector 
        onExperimentSelect={setSelectedExperiment}
        selectedExperiment={selectedExperiment}
      />

      {selectedExperiment ? (
        <>
          {/* Processing Stages Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Processing Pipeline Stages</CardTitle>
              <CardDescription>
                Data at each stage of the pipeline for {selectedExperiment.name}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {processingStages.map((stage) => (
                  <div 
                    key={stage.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedStage === stage.id 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => setSelectedStage(stage.id)}
                  >
                    <h3 className="font-semibold text-sm">{stage.name}</h3>
                    <p className="text-xs text-gray-500 mt-1">{stage.count} files</p>
                    <p className="text-xs text-gray-500">{stage.size}</p>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="mt-2 w-full text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        downloadFile(stage.id, 'files');
                      }}
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Download
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Visualization Tabs */}
          <Tabs defaultValue="waveform" className="space-y-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="waveform" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Waveform
              </TabsTrigger>
              <TabsTrigger value="spectrogram" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Spectrogram
              </TabsTrigger>
              <TabsTrigger value="features" className="flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Features
              </TabsTrigger>
              <TabsTrigger value="embeddings" className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Embeddings
              </TabsTrigger>
            </TabsList>

            {/* Waveform Visualization */}
            <TabsContent value="waveform">
              <Card>
                <CardHeader>
                  <CardTitle>Audio Waveform</CardTitle>
                  <CardDescription>
                    Time-domain representation of the audio signal
                    <Badge variant="outline" className="ml-2">{selectedStage}</Badge>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64 mb-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={waveformData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="time" 
                          label={{ value: 'Time (s)', position: 'insideBottom', offset: -10 }}
                        />
                        <YAxis 
                          label={{ value: 'Amplitude', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip />
                        <Line 
                          type="monotone" 
                          dataKey="amplitude" 
                          stroke="#2563eb" 
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={toggleAudioPlayback}>
                      {isPlaying ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                      {isPlaying ? 'Pause' : 'Play'} Audio
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => downloadFile(selectedStage, 'wav')}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download WAV
                    </Button>
                  </div>
                  <audio ref={audioRef} src="/api/placeholder-audio.wav" />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Keep existing tabs (spectrogram, features, embeddings) the same */}
            <TabsContent value="spectrogram">
              <Card>
                <CardHeader>
                  <CardTitle>Frequency Spectrum</CardTitle>
                  <CardDescription>
                    Frequency-domain representation showing spectral content
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={spectrogramData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="frequency" 
                          label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -10 }}
                        />
                        <YAxis 
                          label={{ value: 'Magnitude (dB)', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip />
                        <Bar dataKey="magnitude" fill="#10b981" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="features">
              <Card>
                <CardHeader>
                  <CardTitle>MFCC Features</CardTitle>
                  <CardDescription>
                    Mel-frequency cepstral coefficients extracted from audio
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={mfccData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="coefficient" 
                          label={{ value: 'MFCC Coefficient', position: 'insideBottom', offset: -10 }}
                        />
                        <YAxis 
                          label={{ value: 'Value', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip />
                        <Bar dataKey="value" fill="#8b5cf6" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-600">13</p>
                      <p className="text-sm text-gray-500">MFCC Coefficients</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-600">256</p>
                      <p className="text-sm text-gray-500">Spectral Features</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-purple-600">12</p>
                      <p className="text-sm text-gray-500">Chroma Features</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="embeddings">
              <Card>
                <CardHeader>
                  <CardTitle>UMAP Embeddings</CardTitle>
                  <CardDescription>
                    2D visualization of high-dimensional audio features for scene analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart data={embeddingData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          type="number"
                          dataKey="x" 
                          label={{ value: 'UMAP Dimension 1', position: 'insideBottom', offset: -10 }}
                        />
                        <YAxis 
                          type="number"
                          dataKey="y"
                          label={{ value: 'UMAP Dimension 2', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip />
                        <Scatter 
                          dataKey="y" 
                          fill="#f59e0b"
                          r={3}
                        />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Badge variant="outline">Cluster 1: Urban Noise</Badge>
                    <Badge variant="outline">Cluster 2: Natural Sounds</Badge>
                    <Badge variant="outline">Cluster 3: Music</Badge>
                    <Badge variant="outline">Cluster 4: Speech</Badge>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* File Browser */}
          <Card>
            <CardHeader>
              <CardTitle>Experiment File Browser</CardTitle>
              <CardDescription>
                Browse and download files from {selectedExperiment.name} stages
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-sm font-mono text-gray-600">
                  /experiments/{selectedExperiment.name?.toLowerCase().replace(/\s+/g, '_')}/
                </div>
                {[
                  { name: "raw/", type: "folder", size: "2.3 GB", count: "1,247 files" },
                  { name: "chunked/", type: "folder", size: "2.1 GB", count: "1,224 files" },
                  { name: "augmented/", type: "folder", size: "6.2 GB", count: "3,603 files" },
                  { name: "model/cnn_classifier.pth", type: "file", size: "45 MB", count: "" },
                  { name: "logs/experiment.log", type: "file", size: "2.1 MB", count: "" },
                  { name: "config.yaml", type: "file", size: "1.2 KB", count: "" }
                ].map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <FileAudio className="h-4 w-4 text-gray-400" />
                      <div>
                        <p className="font-medium text-sm">{item.name}</p>
                        <p className="text-xs text-gray-500">{item.size} {item.count}</p>
                      </div>
                    </div>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => downloadFile('files', item.name)}
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Download
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileAudio className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Experiment Selected</h3>
            <p className="text-gray-500 text-center">
              Please select an experiment above to view data and results.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
