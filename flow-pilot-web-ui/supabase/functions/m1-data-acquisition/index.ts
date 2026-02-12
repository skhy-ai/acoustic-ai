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
    const path = url.pathname.split('/').pop();

    console.log(`M1 Data Acquisition - ${req.method} ${path}`);

    // GET /m1/sensors
    if (req.method === 'GET' && path === 'sensors') {
      const sensors = [
        { type: 'MEMS', settings: { sampleRate: 48000, bitDepth: 24 } },
        { type: 'ultrasonic', settings: { frequency: 40000 } },
        { type: 'hydrophone', settings: { sensitivity: -170 } }
      ];
      
      return new Response(JSON.stringify(sensors), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST requests
    const body = await req.json();

    // POST /m1/streaming
    if (path === 'streaming') {
      const { service, url } = body;
      console.log(`Starting streaming from ${service}: ${url}`);
      
      return new Response(JSON.stringify({
        sessionId: crypto.randomUUID(),
        status: 'started',
        message: `Streaming initiated from ${service}`
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST /m1/format-conversion
    if (path === 'format-conversion') {
      const { inputFormat, outputFormat, bitrate } = body;
      console.log(`Converting from ${inputFormat} to ${outputFormat}`);
      
      return new Response(JSON.stringify({
        fileUrl: `/converted/${crypto.randomUUID()}.${outputFormat}`,
        message: 'Conversion completed'
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST /m1/beamforming
    if (path === 'beamforming') {
      const { method, config } = body;
      console.log(`Applying beamforming: ${method}`);
      
      return new Response(JSON.stringify({
        fileUrl: `/beamformed/${crypto.randomUUID()}.wav`,
        method,
        status: 'completed'
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // POST /m1/multi-device
    if (path === 'multi-device') {
      const { deviceIds, duration } = body;
      console.log(`Multi-device capture: ${deviceIds.length} devices, ${duration}s`);
      
      return new Response(JSON.stringify({
        sessionId: crypto.randomUUID(),
        devices: deviceIds.length,
        status: 'recording'
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Endpoint not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error: any) {
    console.error('M1 Error:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
