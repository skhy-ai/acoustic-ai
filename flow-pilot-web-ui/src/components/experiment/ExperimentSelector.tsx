
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { experimentService, type Experiment } from "@/services/experimentService";
import { Beaker, Calendar, Settings } from "lucide-react";

interface ExperimentSelectorProps {
  onExperimentSelect: (experiment: Experiment | null) => void;
  selectedExperiment?: Experiment | null;
}

export function ExperimentSelector({ onExperimentSelect, selectedExperiment }: ExperimentSelectorProps) {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    try {
      setLoading(true);
      const data = await experimentService.getExperiments();
      setExperiments(data);
    } catch (error) {
      console.error('Error loading experiments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExperimentChange = (experimentId: string) => {
    const experiment = experiments.find(exp => exp.id === experimentId);
    onExperimentSelect(experiment || null);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Beaker className="h-5 w-5" />
          Select Experiment
        </CardTitle>
        <CardDescription>Choose an experiment to view data and results</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Select 
          value={selectedExperiment?.id || ""} 
          onValueChange={handleExperimentChange}
          disabled={loading}
        >
          <SelectTrigger>
            <SelectValue placeholder={loading ? "Loading experiments..." : "Select an experiment"} />
          </SelectTrigger>
          <SelectContent>
            {experiments.map((experiment) => (
              <SelectItem key={experiment.id} value={experiment.id}>
                <div className="flex items-center justify-between w-full">
                  <div>
                    <div className="font-medium">{experiment.name}</div>
                    <div className="text-xs text-gray-500">
                      Created: {new Date(experiment.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <Badge variant={experiment.status === 'configured' ? 'default' : 'secondary'} className="ml-2">
                    {experiment.status}
                  </Badge>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {selectedExperiment && (
          <div className="p-4 border rounded-lg bg-gray-50">
            <div className="flex items-start gap-3">
              <Settings className="h-5 w-5 text-gray-500 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold">{selectedExperiment.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{selectedExperiment.description}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(selectedExperiment.created_at).toLocaleDateString()}
                  </div>
                  <Badge variant="outline">
                    {selectedExperiment.configuration?.modules?.length || 0} modules
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        )}

        <Button variant="outline" onClick={loadExperiments} disabled={loading} className="w-full">
          Refresh Experiments
        </Button>
      </CardContent>
    </Card>
  );
}
