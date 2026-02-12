import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    const endpoint = url.pathname.split('/').pop();
    const body = await req.json();

    console.log(`M3 Augmentation - POST ${endpoint}`);

    // POST /m3/pitch-shift
    if (endpoint === 'pitch-shift') {
      const { fileUrls, range, steps } = body;
      console.log(`Pitch shifting ${fileUrls.length} files: ${range} semitones in ${steps} steps`);
      
      const augmentedFiles = fileUrls.flatMap((url: string) =>
        Array.from({ length: steps }, (_, i) => 
          `/augmented/pitch_${i}_${crypto.randomUUID()}.wav`
        )
      );
      
      return new Response(JSON.stringify({ augmentedFiles }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST /m3/noise-injection
    if (endpoint === 'noise-injection') {
      const { fileUrls, noiseLevel, noiseType } = body;
      console.log(`Injecting ${noiseType} noise at level ${noiseLevel}`);
      
      const augmentedFiles = fileUrls.map((url: string) =>
        `/augmented/noise_${noiseType}_${crypto.randomUUID()}.wav`
      );
      
      return new Response(JSON.stringify({ augmentedFiles }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST /m3/time-stretch
    if (endpoint === 'time-stretch') {
      const { fileUrls, factors, preservePitch } = body;
      console.log(`Time stretching: ${factors} ${preservePitch ? 'preserving pitch' : ''}`);
      
      const augmentedFiles = fileUrls.flatMap((url: string) =>
        [factors[0], factors[1]].map(factor =>
          `/augmented/stretch_${factor}x_${crypto.randomUUID()}.wav`
        )
      );
      
      return new Response(JSON.stringify({ augmentedFiles }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST /m3/volume-adjustment
    if (endpoint === 'volume-adjustment') {
      const { fileUrls, range, fadeIn, fadeOut } = body;
      console.log(`Volume adjustment: ${range} dB`);
      
      const augmentedFiles = fileUrls.map((url: string) =>
        `/augmented/volume_${crypto.randomUUID()}.wav`
      );
      
      return new Response(JSON.stringify({ augmentedFiles }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST /m3/spectral-augmentation
    if (endpoint === 'spectral-augmentation') {
      const { fileUrls, freqMasking, timeMasking } = body;
      console.log(`Spectral augmentation: ${freqMasking.numMasks} freq masks, ${timeMasking.numMasks} time masks`);
      
      const augmentedFiles = fileUrls.map((url: string) =>
        `/augmented/spectral_${crypto.randomUUID()}.wav`
      );
      
      return new Response(JSON.stringify({ augmentedFiles }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST /m3/pipeline
    if (endpoint === 'pipeline') {
      const { fileUrls, pipeline } = body;
      console.log(`Augmentation pipeline with ${pipeline.length} steps`);
      
      const augmentedFiles = fileUrls.map((url: string) =>
        `/augmented/pipeline_${crypto.randomUUID()}.wav`
      );
      
      const augmentationMap: Record<string, string[]> = {};
      fileUrls.forEach((url: string, i: number) => {
        augmentationMap[url] = [augmentedFiles[i]];
      });
      
      return new Response(JSON.stringify({ augmentedFiles, augmentationMap }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Endpoint not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error: any) {
    console.error('M3 Error:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
