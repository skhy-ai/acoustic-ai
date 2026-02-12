import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { User } from "@supabase/supabase-js";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { ExperimentBuilder } from "@/components/experiment/ExperimentBuilder";
import { ParameterEditor } from "@/components/experiment/ParameterEditor";
import { LiveMonitor } from "@/components/experiment/LiveMonitor";
import { DataViewer } from "@/components/experiment/DataViewer";
import { ExecutionEngine } from "@/components/experiment/ExecutionEngine";
import { Auth } from "@/components/Auth";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

const Index = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState("builder");
  const [currentExperiment, setCurrentExperiment] = useState(null);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <Auth />;
  }

  const renderActiveView = () => {
    switch (activeView) {
      case "builder":
        return <ExperimentBuilder onExperimentChange={setCurrentExperiment} />;
      case "parameters":
        return <ParameterEditor experiment={currentExperiment} />;
      case "monitor":
        return <LiveMonitor />;
      case "data":
        return <DataViewer />;
      case "execution":
        return <ExecutionEngine experiment={currentExperiment} />;
      default:
        return <ExperimentBuilder onExperimentChange={setCurrentExperiment} />;
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-gray-50">
        <AppSidebar activeView={activeView} onViewChange={setActiveView} />
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            <header className="mb-8 flex justify-between items-center">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                  Skhy Acoustic AI Platform
                </h1>
                <p className="text-lg text-gray-600">
                  Build, configure, and execute acoustic AI workflows dynamically
                </p>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">
                  Welcome, {user.email}
                </span>
                <Button 
                  variant="outline" 
                  onClick={handleSignOut}
                  className="flex items-center gap-2"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </Button>
              </div>
            </header>
            {renderActiveView()}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
};

export default Index;
