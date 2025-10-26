import './App.css'
import { Calendar } from "@/components/ui/calendar";
import { Button } from "@/components/ui/button";
import { useState, useEffect, useCallback } from "react";
import type { DateRange } from "react-day-picker";
import { Check, Circle, Dot, CornerUpLeft, TriangleAlert } from "lucide-react";
import { 
  Stepper, 
  StepperItem, 
  StepperSeparator, 
  StepperTrigger, 
  StepperTitle, 
  StepperDescription,
  getSegmentRiskScore,
  primeCrashSummariesForSegments
} from "@/components/ui/stepper";
import type { SegmentRiskScore, StepperSegmentInfo } from "@/components/ui/stepper";
import MapboxExample from "@/components/MapboxExample";
import { RouteOptimizationForm } from "@/components/RouteOptimizationForm";
import { apiService } from "@/services/api";
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

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
  const [segmentRiskMap, setSegmentRiskMap] = useState<Record<string, SegmentRiskScore | null>>({});
  const getSegmentKey = useCallback((segment?: RouteSegment) => {
    if (!segment) return "segment-unknown";
    const legPart = segment.leg_index != null ? `leg-${segment.leg_index}` : "leg-x";
    const stepPart = segment.step_index != null ? `step-${segment.step_index}` : "step-x";

    if (segment.coordinates && segment.coordinates.length > 0) {
      const first = segment.coordinates[0];
      const last = segment.coordinates[segment.coordinates.length - 1];
      return `${legPart}-${stepPart}-${first[0].toFixed(5)},${first[1].toFixed(5)}-${last[0].toFixed(5)},${last[1].toFixed(5)}`;
    }

    if (segment.instruction) {
      return `${legPart}-${stepPart}-${segment.instruction.slice(0, 32)}`;
    }

    return `${legPart}-${stepPart}-${segment.distance_meters ?? "dist"}`;
  }, []);
  type StepDefinition = {
    step: number;
    title: string;
    description: string;
    segment?: RouteSegment;
    segmentRisk?: SegmentRiskScore | null;
    totalRisk?: number;
  };

  // Reset to step 1 when route changes
  useEffect(() => {
    setCurrentStep(1);
  }, [origin?.address, destination?.address, stops?.length, legs?.length, segments?.length]);

  useEffect(() => {
    let cancelled = false;

    const computeSegmentRisks = async () => {
      if (!segments || segments.length === 0) {
        if (!cancelled) {
          setSegmentRiskMap({});
        }
        return;
      }

      if (!cancelled) {
        setSegmentRiskMap({});
      }

      const stepperSegments: StepperSegmentInfo[] = segments.map((segment) => ({
        leg_index: segment.leg_index,
        step_index: segment.step_index,
        coordinates: segment.coordinates,
        distance_meters: segment.distance_meters,
        duration_seconds: segment.duration_seconds,
        duration_in_traffic_seconds: segment.duration_in_traffic_seconds,
        travel_mode: segment.travel_mode,
        instruction: segment.instruction,
      }));

      await primeCrashSummariesForSegments(stepperSegments);

      const results = await Promise.all(
        stepperSegments.map(async (segmentInfo, index) => {
          const segment = segments[index];
          const key = getSegmentKey(segment);
          try {
            const risk = await getSegmentRiskScore(segmentInfo);
            return [key, risk] as const;
          } catch (error) {
            console.error("Failed to calculate segment risk", error);
            return [key, null] as const;
          }
        })
      );

      if (!cancelled) {
        const mapped = Object.fromEntries(results) as Record<string, SegmentRiskScore | null>;
        setSegmentRiskMap(mapped);
      }
    };

    computeSegmentRisks();

    return () => {
      cancelled = true;
    };
  }, [segments, getSegmentKey]);

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
          let incidentCount = 0;

          for (const seg of legSegments) {
            const riskData = segmentRiskMap[getSegmentKey(seg)];
            if (riskData?.score != null) {
              totalRisk += riskData.score;
            }
            if (riskData?.crashCount) {
              incidentCount += riskData.crashCount;
            }
          }

          if (incidentCount > 0) {
            descriptionParts.push(`${incidentCount} nearby incidents`);
          }

          const roundedRisk = totalRisk > 0 ? Math.round(totalRisk) : incidentCount > 0 ? 0 : undefined;

          return {
            step: index + 1,
            title: `Leg ${entry.leg.leg_index + 1}: ${formatAddress(entry.leg.start_address)} → ${formatAddress(entry.leg.end_address)}`,
            description: descriptionParts.length > 0
              ? descriptionParts.join(" • ")
              : "Distance and duration unavailable",
            segment: undefined,
            segmentRisk: undefined,
            totalRisk: roundedRisk,
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

        const segmentRisk = segmentRiskMap[getSegmentKey(segment)] ?? null;
        if (segmentRisk?.crashCount) {
          segmentParts.push(`${segmentRisk.crashCount} nearby incidents`);
        }

        return {
          step: index + 1,
          title: `Segment ${segment.step_index + 1}`,
          description: segmentParts.length > 0 ? segmentParts.join(" • ") : "Segment details unavailable",
          segment,
          segmentRisk,
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
        segmentRisk: undefined,
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
          segmentRisk: undefined,
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
        segmentRisk: undefined,
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
          segmentRisk: undefined,
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
            <StepperItem
              key={step.step}
              step={step.step}
              segmentInfo={step.segment}
              totalRisk={step.totalRisk}
            >
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
                    {leftTurnRisk && step.segmentRisk?.crashCount && step.segmentRisk.crashCount >= 3 && (
                      <>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="inline-flex items-center justify-center py-1 px-1 bg-red-50 border border-red-200 rounded">
                              <CornerUpLeft className="w-3 h-3 text-red-500" strokeWidth={3} />
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Left turn ahead - High risk area</p>
                          </TooltipContent>
                        </Tooltip>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="inline-flex items-center justify-center py-1 px-1 bg-amber-50 border border-amber-200 rounded ml-1">
                              <TriangleAlert className="w-3 h-3 text-amber-600" />
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{step.segmentRisk.crashCount} historic crashes within 200m</p>
                          </TooltipContent>
                        </Tooltip>
                      </>
                    )}
                    {leftTurnRisk && (!step.segmentRisk?.crashCount || step.segmentRisk.crashCount < 3) && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="inline-flex items-center justify-center py-1 px-1 bg-red-50 border border-red-200 rounded">
                            <CornerUpLeft className="w-3 h-3 text-red-500" strokeWidth={3} />
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Left turn ahead</p>
                        </TooltipContent>
                      </Tooltip>
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
                      {leftTurnRisk && step.segmentRisk?.crashCount && step.segmentRisk.crashCount >= 3 && (
                        <>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="inline-flex items-center justify-center py-1 px-1 bg-red-50 border border-red-200 rounded">
                                <CornerUpLeft className="w-3 h-3 text-red-500" strokeWidth={3} />
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Left turn ahead - High risk area</p>
                            </TooltipContent>
                          </Tooltip>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="inline-flex items-center justify-center py-1 px-1 bg-amber-50 border border-amber-200 rounded ml-1">
                                <TriangleAlert className="w-3 h-3 text-amber-600" />
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{step.segmentRisk.crashCount} historic crashes within 200m</p>
                            </TooltipContent>
                          </Tooltip>
                        </>
                      )}
                      {leftTurnRisk && (!step.segmentRisk?.crashCount || step.segmentRisk.crashCount < 3) && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="inline-flex items-center justify-center py-1 px-1 bg-red-50 border border-red-200 rounded">
                              <CornerUpLeft className="w-3 h-3 text-red-500" strokeWidth={3} />
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Left turn ahead</p>
                          </TooltipContent>
                        </Tooltip>
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

type CrashProximityCrash = {
  crash_fact_id?: string;
  name?: string;
  latitude?: number;
  longitude?: number;
  distance_meters: number;
  crash_datetime?: string;
  collision_type?: string;
  primary_factor?: string;
  lighting?: string;
  weather?: string;
  a_street?: string;
  b_street?: string;
  fatal_injuries?: number;
  severe_injuries?: number;
  moderate_injuries?: number;
  minor_injuries?: number;
  total_injuries?: number;
  speeding_flag?: boolean;
  hit_and_run_flag?: boolean;
};

type CrashProximitySegmentResult = {
  leg_index?: number | null;
  step_index?: number | null;
  instruction?: string;
  travel_mode?: string;
  distance_meters?: number;
  duration_seconds?: number;
  duration_in_traffic_seconds?: number;
  close_crash_count: number;
  min_distance_meters?: number | null;
  close_crashes: CrashProximityCrash[];
};

type CrashProximityLegSummary = {
  leg_index: number;
  segment_count: number;
  segments_with_crashes: number;
  total_close_crashes: number;
  min_distance_meters?: number | null;
};

type CrashProximityAnalysis = {
  success: boolean;
  threshold_meters: number;
  segment_count: number;
  segments_with_crashes: number;
  total_close_crashes: number;
  segments: CrashProximitySegmentResult[];
  legs_summary: CrashProximityLegSummary[];
  error?: string;
};

function CrashDataDemo({
  legs,
  segments
}: {
  legs?: RouteLeg[];
  segments?: RouteSegment[];
}) {
  const [analysis, setAnalysis] = useState<CrashProximityAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const thresholdMeters = 200;
  const segmentsCount = segments?.length ?? 0;
  const legsCount = legs?.length ?? 0;

  useEffect(() => {
    setAnalysis(null);
    setError(null);
  }, [segmentsCount, legsCount]);

  const stripHtml = (value?: string) =>
    value ? value.replace(/<[^>]+>/g, "").replace(/&nbsp;/g, " ").trim() : "";

  const formatCrashTime = (value?: string) => {
    if (!value) return "Unknown time";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return parsed.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit"
    });
  };

  const formatInjurySummary = (crash: CrashProximityCrash) => {
    const parts: string[] = [];
    if (crash.fatal_injuries) parts.push(`${crash.fatal_injuries} fatal`);
    if (crash.severe_injuries) parts.push(`${crash.severe_injuries} severe`);
    if (crash.moderate_injuries) parts.push(`${crash.moderate_injuries} moderate`);
    if (crash.minor_injuries) parts.push(`${crash.minor_injuries} minor`);
    if (!parts.length && crash.total_injuries) {
      parts.push(`${crash.total_injuries} injuries`);
    }
    if (!parts.length) {
      return "No injuries reported";
    }
    return parts.join(", ");
  };

  const formatLegLabel = (legIndex?: number | null) => {
    if (legIndex === null || legIndex === undefined) {
      return "Segment";
    }
    const leg = legs?.find((item) => item.leg_index === legIndex);
    if (!leg) {
      return `Leg ${legIndex + 1}`;
    }
    const start = leg.start_address?.split(",")[0] ?? "Start";
    const end = leg.end_address?.split(",")[0] ?? "End";
    return `Leg ${legIndex + 1}: ${start} → ${end}`;
  };

  const formatMiles = (meters?: number) => {
    if (!meters) return null;
    return `${(meters * 0.000621371).toFixed(2)} mi`;
  };

  const formatDurationMinutes = (segment: CrashProximitySegmentResult) => {
    const durationSeconds = segment.duration_in_traffic_seconds ?? segment.duration_seconds;
    if (!durationSeconds) {
      return null;
    }
    return `${Math.round(durationSeconds / 60)} min`;
  };

  const handleAnalyze = async () => {
    if (!segments || segments.length === 0) {
      setError("Load a Google Maps route to analyze crash exposure.");
      setAnalysis(null);
      return;
    }

    const payloadSegments = segments
      .filter((segment) => Array.isArray(segment.coordinates) && segment.coordinates.length >= 2)
      .map((segment) => ({
        leg_index: segment.leg_index,
        step_index: segment.step_index,
        coordinates: segment.coordinates,
        distance_meters: segment.distance_meters,
        duration_seconds: segment.duration_seconds,
        duration_in_traffic_seconds: segment.duration_in_traffic_seconds,
        instruction: segment.instruction,
        travel_mode: segment.travel_mode,
      }));

    if (payloadSegments.length === 0) {
      setError("Route segments are missing geometry data.");
      setAnalysis(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response: CrashProximityAnalysis = await apiService.analyzeCrashProximity({
        segments: payloadSegments,
        threshold_meters: thresholdMeters,
        max_crashes_per_segment: 5
      });

      if (!response.success) {
        setError(response.error || "Crash proximity analysis failed.");
        setAnalysis(null);
        return;
      }

      setAnalysis(response);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Crash proximity analysis failed.");
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button onClick={handleAnalyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Crash Proximity"}
          </Button>
          <span className="text-xs text-muted-foreground">
            Within {thresholdMeters} m of the route using 13k historic crashes
          </span>
        </div>
        <div className="text-xs text-muted-foreground">
          Powered by Shapely spatial buffers and STRtree search
        </div>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {analysis && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="rounded-md border p-3">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Segments analyzed</div>
              <div className="text-2xl font-semibold">{analysis.segment_count}</div>
            </div>
            <div className="rounded-md border p-3">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Segments with crashes</div>
              <div className="text-2xl font-semibold">{analysis.segments_with_crashes}</div>
            </div>
            <div className="rounded-md border p-3">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Incidents flagged</div>
              <div className="text-2xl font-semibold">{analysis.total_close_crashes}</div>
            </div>
          </div>

          {analysis.legs_summary.length > 0 && (
            <div className="rounded-md border p-4 space-y-2">
              <div className="text-sm font-semibold">Leg breakdown</div>
              {analysis.legs_summary.map((leg) => (
                <div key={leg.leg_index} className="rounded border border-dashed p-2 text-sm">
                  <div className="font-medium">{formatLegLabel(leg.leg_index)}</div>
                  <div className="text-xs text-muted-foreground">
                    {leg.segments_with_crashes} / {leg.segment_count} segments within {analysis.threshold_meters} m
                    {leg.min_distance_meters !== null && leg.min_distance_meters !== undefined && (
                      <> • nearest {leg.min_distance_meters.toFixed(1)} m</>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {leg.total_close_crashes} nearby incidents
                  </div>
                </div>
              ))}
            </div>
          )}

          {analysis.segments.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No historic crash incidents found within {analysis.threshold_meters} meters of this route.
            </p>
          )}

          {analysis.segments.length > 0 && (
            <div className="space-y-4">
              {analysis.segments.map((segment) => (
                <div
                  key={`${segment.leg_index ?? 'na'}-${segment.step_index ?? 'na'}`}
                  className="rounded-md border p-4 space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold">{formatLegLabel(segment.leg_index)}</div>
                      <div className="text-xs text-muted-foreground">
                        Segment {segment.step_index !== null && segment.step_index !== undefined ? segment.step_index + 1 : "?"}
                        {segment.instruction && (
                          <> • {stripHtml(segment.instruction)}</>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {[formatMiles(segment.distance_meters), formatDurationMinutes(segment)].filter(Boolean).join(" • ") || "Distance unavailable"}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold">{segment.close_crash_count} incidents</div>
                      {segment.min_distance_meters !== null && segment.min_distance_meters !== undefined && (
                        <div className="text-xs text-muted-foreground">Nearest {segment.min_distance_meters.toFixed(1)} m</div>
                      )}
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="min-w-full text-left text-xs">
                      <thead className="bg-muted/50 text-muted-foreground">
                        <tr>
                          <th className="py-2 pr-4 font-medium">Crash</th>
                          <th className="py-2 pr-4 font-medium">Distance</th>
                          <th className="py-2 pr-4 font-medium">Context</th>
                          <th className="py-2 pr-4 font-medium">Injuries</th>
                        </tr>
                      </thead>
                      <tbody>
                        {segment.close_crashes.map((crash, index) => (
                          <tr key={crash.crash_fact_id ?? index} className="border-t">
                            <td className="py-2 pr-4 align-top">
                              <div className="font-medium">{crash.collision_type || "Collision"}</div>
                              <div className="text-muted-foreground">
                                {formatCrashTime(crash.crash_datetime)}
                              </div>
                              <div className="text-muted-foreground">
                                {crash.a_street || "Unknown"}
                                {crash.b_street ? ` & ${crash.b_street}` : ""}
                              </div>
                            </td>
                            <td className="py-2 pr-4 align-top">
                              {crash.distance_meters.toFixed(1)} m
                            </td>
                            <td className="py-2 pr-4 align-top">
                              <div className="text-muted-foreground">
                                {crash.primary_factor || "Factor unavailable"}
                              </div>
                              <div className="text-muted-foreground">
                                {(crash.weather || "Weather unknown")}
                                {" • "}
                                {(crash.lighting || "Lighting unknown")}
                              </div>
                            </td>
                            <td className="py-2 pr-4 align-top">
                              <div className="text-muted-foreground">{formatInjurySummary(crash)}</div>
                              {(crash.speeding_flag || crash.hit_and_run_flag) && (
                                <div className="text-muted-foreground">
                                  {[crash.speeding_flag ? "Speeding" : null, crash.hit_and_run_flag ? "Hit & run" : null]
                                    .filter(Boolean)
                                    .join(" • ")}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
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
      <NavigationMenu className="w-full px-6 py-4 justify-start">
        <NavigationMenuList>
          <NavigationMenuItem>
            <NavigationMenuLink className="text-4xl font-bold text-left">
              DTS
            </NavigationMenuLink>
          </NavigationMenuItem>
        </NavigationMenuList>
      </NavigationMenu>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
        <div className="space-y-4">
          <RouteOptimizationForm onRouteOptimized={handleRouteOptimized} />
        </div>

        <div className="space-y-4">
          {/* <h2 className="text-2xl font-bold">Route Map</h2> */}
          <div style={{ height: '500px', width: '100%' }}>
            <MapboxExample
              origin={routeData.origin}
              destination={routeData.destination}
              stops={routeData.stops}
              routeCoordinates={routeData.routeCoordinates}
            />
          </div>
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
        <CrashDataDemo legs={routeData.legs} segments={routeData.segments} />
      </div>
    </div>
  );
}

export default App