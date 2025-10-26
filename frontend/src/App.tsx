import './App.css'
import { Calendar } from "@/components/ui/calendar";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import type { DateRange } from "react-day-picker";
import { Check, Circle, Dot, CornerUpLeft } from "lucide-react";
import { 
  Stepper, 
  StepperItem, 
  StepperSeparator, 
  StepperTrigger, 
  StepperTitle, 
  StepperDescription,
  getSegmentRiskScore
} from "@/components/ui/stepper";
import MapboxExample from "@/components/MapboxExample";
import { RouteOptimizationForm } from "@/components/RouteOptimizationForm";

type RouteLeg = {
  leg_index: number;
  start_address: string;
  end_address: string;
  start_location: { lat: number; lng: number };
  end_location: { lat: number; lng: number };
  distance_meters: number;
  duration_seconds: number;
  duration_in_traffic_seconds?: number;
  steps_count: number;
  coordinates: [number, number][];
};

type RouteSegment = {
  leg_index: number;
  step_index: number;
  coordinates: [number, number][];
  distance_meters: number;
  duration_seconds: number;
  duration_in_traffic_seconds?: number;
  instruction: string;
  travel_mode: string;
};

export function CalendarRangeDemo() {
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: new Date(),
    to: new Date(new Date().setDate(new Date().getDate() + 7))
  });
  
  return (
    <Calendar
      mode="range"
      selected={dateRange}
      onSelect={setDateRange}
      className="rounded-md border"
      numberOfMonths={2}
    />
  );
}

function StepperDemo({ 
  origin, 
  destination, 
  stops = [],
  legs = [],
  segments = []
}: {
  origin?: { address: string; coordinates: { lat: number; lng: number } };
  destination?: { address: string; coordinates: { lat: number; lng: number } };
  stops?: { address: string; coordinates: { lat: number; lng: number } }[];
  legs?: RouteLeg[];
  segments?: RouteSegment[];
}) {
  const [currentStep, setCurrentStep] = useState(1);
  type StepDefinition = {
    step: number;
    title: string;
    description: string;
    segment?: RouteSegment;
    totalRisk?: number;
  };

  // Reset to step 1 when route changes
  useEffect(() => {
    setCurrentStep(1);
  }, [origin?.address, destination?.address, stops?.length, legs?.length, segments?.length]);

  // Generate dynamic steps based on actual route
  const generateSteps = () => {
    const formatAddress = (address?: string) => {
      if (!address) return "Waypoint";
      const [label] = address.split(",");
      return label || address;
    };

    if (legs && legs.length > 0) {
      const combined: {
        kind: "leg" | "segment";
        leg: RouteLeg;
        segment?: RouteSegment;
      }[] = [];

      legs.forEach((leg) => {
        combined.push({ kind: "leg", leg });
        const legSegments = (segments || []).filter((segment) => segment.leg_index === leg.leg_index);
        legSegments.forEach((segment) => {
          combined.push({ kind: "segment", leg, segment });
        });
      });

      return combined.map<StepDefinition>((entry, index) => {
        if (entry.kind === "leg") {
          const distanceMiles = entry.leg.distance_meters ? entry.leg.distance_meters * 0.000621371 : 0;
          const durationSeconds = entry.leg.duration_in_traffic_seconds ?? entry.leg.duration_seconds ?? 0;
          const durationMinutes = durationSeconds ? Math.round(durationSeconds / 60) : 0;
          const descriptionParts: string[] = [];

          if (distanceMiles > 0) {
            descriptionParts.push(`${distanceMiles.toFixed(1)} mi`);
          }
          if (durationMinutes > 0) {
            descriptionParts.push(`${durationMinutes} min`);
          }

          const legSegments = (segments || []).filter((segment) => segment.leg_index === entry.leg.leg_index);
          let totalRisk = 0;
          for (const seg of legSegments) {
            const riskData = getSegmentRiskScore({
              distance_meters: seg.distance_meters,
              duration_seconds: seg.duration_seconds,
              duration_in_traffic_seconds: seg.duration_in_traffic_seconds,
              travel_mode: seg.travel_mode,
              instruction: seg.instruction,
            });
            if (riskData.score) totalRisk += riskData.score;
          }

          return {
            step: index + 1,
            title: `Leg ${entry.leg.leg_index + 1}: ${formatAddress(entry.leg.start_address)} → ${formatAddress(entry.leg.end_address)}`,
            description: descriptionParts.length > 0
              ? descriptionParts.join(" • ")
              : "Distance and duration unavailable",
            segment: undefined,
            totalRisk,
          };
        }

        const segment = entry.segment!;
        const segmentDistanceMiles = segment.distance_meters ? segment.distance_meters * 0.000621371 : 0;
        const segmentDurationSeconds = segment.duration_in_traffic_seconds ?? segment.duration_seconds ?? 0;
        const segmentDurationMinutes = segmentDurationSeconds ? Math.round(segmentDurationSeconds / 60) : 0;

        const instruction = segment.instruction
          .replace(/<[^>]+>/g, "")
          .replace(/&nbsp;/g, " ")
          .trim();

        const segmentParts: string[] = [];
        if (instruction) {
          segmentParts.push(instruction);
        }
        if (segmentDistanceMiles > 0) {
          segmentParts.push(`${segmentDistanceMiles.toFixed(1)} mi`);
        }
        if (segmentDurationMinutes > 0) {
          segmentParts.push(`${segmentDurationMinutes} min`);
        }

        return {
          step: index + 1,
          title: `Segment ${segment.step_index + 1}`,
          description: segmentParts.length > 0 ? segmentParts.join(" • ") : "Segment details unavailable",
          segment,
          totalRisk: undefined,
        };
      });
    }

    const steps: StepDefinition[] = [];
    let stepNumber = 1;

    // Add origin as first step
    if (origin) {
      steps.push({
        step: stepNumber++,
        title: `Pickup at ${origin.address.split(',')[0]}`,
        description: `Package collected from ${origin.address}`,
        segment: undefined,
        totalRisk: undefined,
      });
    }

    // Add each stop
    if (stops && stops.length > 0) {
      stops.forEach((stop, index) => {
        steps.push({
          step: stepNumber++,
          title: `Stop ${index + 1}: ${stop.address.split(',')[0]}`,
          description: `Delivery stop at ${stop.address}`,
          segment: undefined,
          totalRisk: undefined,
        });
      });
    }

    // Add destination as last step
    if (destination) {
      steps.push({
        step: stepNumber++,
        title: `Delivery at ${destination.address.split(',')[0]}`,
        description: `Final destination: ${destination.address}`,
        segment: undefined,
        totalRisk: undefined,
      });
    }

    // If no route is set, show placeholder
    if (steps.length === 0) {
      return [
        {
          step: 1,
          title: "No Route Selected",
          description: "Please enter origin and destination to see steps",
          segment: undefined,
          totalRisk: undefined,
        }
      ];
    }

    return steps;
  };

  const steps = generateSteps();

  const getStepState = (stepNumber: number) => {
    if (stepNumber < currentStep) return "completed";
    if (stepNumber === currentStep) return "active";
    return "inactive";
  };

  return (
    <div className="relative">
      <Stepper className="mx-auto w-[56rem]">
        {steps.map((step, index) => {
          const state = getStepState(step.step);
          const isLastStep = index === steps.length - 1;
          const leftTurnRisk = step.segment?.instruction?.includes("Turn <b>left</b>") ?? false;

          return (
            <StepperItem key={step.step} step={step.step} segmentInfo={step.segment} totalRisk={step.totalRisk}>
              {!isLastStep && <StepperSeparator />}

              <StepperTrigger>
                <Button
                  variant={state === "completed" || state === "active" ? "default" : "outline"}
                  size="icon"
                  className={`rounded-full shrink-0 ${
                    state === "active" ? "ring-2 ring-ring ring-offset-2 ring-offset-background" : ""
                  }`}
                  onClick={() => setCurrentStep(step.step)}
                >
                  {state === "completed" && <Check className="size-5" />}
                  {state === "active" && <Circle className="size-4" />}
                  {state === "inactive" && <Dot className="size-4" />}
                </Button>
              </StepperTrigger>

              <div className="flex flex-col gap-1 mr-48">
                {step.segment ? (
                  <div className="flex flex-row items-center gap-2">
                    <StepperDescription
                      className={state === "active" ? "text-primary" : ""}
                    >
                      {step.description}
                    </StepperDescription>
                    {leftTurnRisk && (
                      <span className="inline-flex items-center justify-center py-1 px-1 bg-red-50 border border-red-200 rounded">
                        <CornerUpLeft className="w-3 h-3 text-red-500" strokeWidth={3} />
                      </span>
                    )}
                  </div>
                ) : (
                  <>
                    <div className="flex flex-row items-center gap-2">
                      <StepperTitle
                        className={state === "active" ? "text-primary" : ""}
                      >
                        {step.title}
                      </StepperTitle>
                      {leftTurnRisk && (
                        <span className="inline-flex items-center justify-center py-1 px-1 bg-red-50 border border-red-200 rounded">
                          <CornerUpLeft className="w-3 h-3 text-red-500" strokeWidth={3} />
                        </span>
                      )}
                    </div>
                    <StepperDescription
                      className={state === "active" ? "text-primary" : ""}
                    >
                      {step.description}
                    </StepperDescription>
                  </>
                )}
              </div>
            </StepperItem>
          );
        })}
      </Stepper>
    </div>
  );
}

function CrashDataDemo() {
  const [data, setData] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCrashData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:5001/api/crash-data');
      const result = await response.json();
      if (result.success) {
        setData(result.data);
      } else {
        setError(result.error);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="crash-data-demo">
      <Button onClick={fetchCrashData} disabled={loading}>
        {loading ? 'Loading...' : 'Fetch Crash Data'}
      </Button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {data.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h3>First 100 Crash Records</h3>
          <table style={{ borderCollapse: 'collapse', width: '100%' }}>
            <thead>
              <tr>
                {Object.keys(data[0]).map(key => (
                  <th key={key} style={{ border: '1px solid #ddd', padding: '8px' }}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((record, index) => (
                <tr key={index}>
                  {Object.values(record).map((value, i) => (
                    <td key={i} style={{ border: '1px solid #ddd', padding: '8px' }}>{String(value)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function App() {
  const [routeData, setRouteData] = useState<{
    origin?: { address: string; coordinates: { lat: number; lng: number } };
    destination?: { address: string; coordinates: { lat: number; lng: number } };
    stops?: { address: string; coordinates: { lat: number; lng: number } }[];
    routeCoordinates?: [number, number][]; // TomTom optimized route
    legs?: RouteLeg[];
    segments?: RouteSegment[];
  }>({});

  const handleRouteOptimized = (route: {
    origin: { address: string; coordinates: { lat: number; lng: number } };
    destination: { address: string; coordinates: { lat: number; lng: number } };
    stops: { address: string; coordinates: { lat: number; lng: number } }[];
    routeCoordinates?: [number, number][];
    legs?: RouteLeg[];
    segments?: RouteSegment[];
  }) => {
    setRouteData(route);
  };

  return (
    <div className="landing-page">
      <h1>DTS - Delivery Time Slot Optimization</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
        <div className="space-y-4">
          <RouteOptimizationForm onRouteOptimized={handleRouteOptimized} />
        </div>

        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Select Delivery Window</h2>
          <CalendarRangeDemo />
        </div>
      </div>

      <div className="px-6 pb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Route Map</h2>
          <p className="text-sm text-muted-foreground">
            🟢 Green route = Real road network with traffic
          </p>
        </div>
        <div style={{ height: '700px', width: '100%' }}>
          <MapboxExample
            origin={routeData.origin}
            destination={routeData.destination}
            stops={routeData.stops}
            routeCoordinates={routeData.routeCoordinates}
          />
        </div>
      </div>

      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Steps</h2>
        <StepperDemo 
          origin={routeData.origin}
          destination={routeData.destination}
          stops={routeData.stops}
          legs={routeData.legs}
          segments={routeData.segments}
        />
      </div>

      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Crash Hotspots</h2>
        <CrashDataDemo />
      </div>
    </div>
  );
}

export default App