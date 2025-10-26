/* eslint-disable react-refresh/only-export-components */
import * as React from "react"
import { cn } from "@/lib/utils"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { apiService } from "@/services/api"

interface StepperContextValue {
  currentStep: number
  setCurrentStep: (step: number) => void
}

const StepperContext = React.createContext<StepperContextValue | undefined>(undefined)

export type StepperSegmentInfo = {
  leg_index?: number
  step_index?: number
  coordinates?: [number, number][]
  distance_meters?: number
  duration_seconds?: number
  duration_in_traffic_seconds?: number
  travel_mode?: string
  instruction?: string
}

type CrashProximitySummary = {
  close_crash_count?: number
  min_distance_meters?: number | null
}

export type SegmentRiskScore = {
  score: number | null
  leftTurnRisk: boolean
  crashCount: number
  crashProximityScore: number
  minCrashDistance?: number | null
}

// RISK SCORES, SCORING, WEIGHTING, CONSTANTS
const RISK_SCORE_LEFT_TURN = 10
const DEFAULT_CRASH_THRESHOLD_METERS = 200

const crashSummaryCache = new Map<string, Promise<CrashProximitySummary | null>>()

const getSegmentCacheKey = (segment: StepperSegmentInfo) => {
  const legPart = segment.leg_index != null ? `leg-${segment.leg_index}` : "leg-x"
  const stepPart = segment.step_index != null ? `step-${segment.step_index}` : "step-x"
  if (segment.coordinates && segment.coordinates.length > 0) {
    const coordPart = segment.coordinates
      .map(([lng, lat]) => `${lng.toFixed(5)},${lat.toFixed(5)}`)
      .join("|")
    return `${legPart}-${stepPart}-${coordPart}`
  }
  const distancePart = segment.distance_meters ? `dist-${Math.round(segment.distance_meters)}` : "dist-x"
  const instructionPart = segment.instruction ? segment.instruction.slice(0, 40) : "instr-x"
  return `${legPart}-${stepPart}-${distancePart}-${instructionPart}`
}

const fetchCrashSummaryForSegment = async (segment: StepperSegmentInfo): Promise<CrashProximitySummary | null> => {
  if (!segment.coordinates || segment.coordinates.length < 2) {
    return null
  }

  const cacheKey = getSegmentCacheKey(segment)

  if (!crashSummaryCache.has(cacheKey)) {
    const payloadSegment = {
      leg_index: segment.leg_index,
      step_index: segment.step_index,
      coordinates: segment.coordinates,
      distance_meters: segment.distance_meters,
      duration_seconds: segment.duration_seconds,
      duration_in_traffic_seconds: segment.duration_in_traffic_seconds,
      instruction: segment.instruction,
      travel_mode: segment.travel_mode
    }

    const summaryPromise = apiService
      .analyzeCrashProximity({
        segments: [payloadSegment],
        threshold_meters: DEFAULT_CRASH_THRESHOLD_METERS,
        max_crashes_per_segment: 5
      })
      .then((response) => {
        if (response && response.success && Array.isArray(response.segments) && response.segments.length > 0) {
          const [segmentSummary] = response.segments
          return {
            close_crash_count: segmentSummary?.close_crash_count ?? 0,
            min_distance_meters: segmentSummary?.min_distance_meters ?? null
          }
        }
        return null
      })
      .catch(() => null)

    crashSummaryCache.set(cacheKey, summaryPromise)
  }

  const cached = crashSummaryCache.get(cacheKey)
  if (!cached) {
    return null
  }
  return cached
}

export async function getSegmentRiskScore(segment: StepperSegmentInfo): Promise<SegmentRiskScore> {
  const distanceMeters = segment.distance_meters ?? 0
  const durationSeconds = segment.duration_in_traffic_seconds ?? segment.duration_seconds ?? 0

  if (distanceMeters === 0 && durationSeconds === 0) {
    return {
      score: null,
      leftTurnRisk: false,
      crashCount: 0,
      crashProximityScore: 0,
      minCrashDistance: null
    }
  }

  // Basic heuristic weighting segment distance, time, speed, and travel mode.
  const distanceScore = Math.min(distanceMeters / 100, 40)
  const durationScore = Math.min(durationSeconds / 30, 40)
  const averageSpeedMps = durationSeconds > 0 ? distanceMeters / durationSeconds : 0
  const averageSpeedMph = averageSpeedMps * 2.23694
  const speedScore = averageSpeedMph > 45 ? Math.min((averageSpeedMph - 45) / 5 * 5, 15) : 0

  const mode = segment.travel_mode?.toLowerCase()
  const modeAdjustment = mode === "driving" ? 5 : mode === "cycling" ? 3 : mode === "walking" ? 1 : 2

  let rawScore = distanceScore * 0.4 + durationScore * 0.3 + speedScore * 0.2 + modeAdjustment
  let leftTurnRisk = false

  // Add risk for left turns
  if (segment.instruction?.includes("Turn <b>left</b>")) {
    rawScore += RISK_SCORE_LEFT_TURN
    leftTurnRisk = true
  }

  let crashCount = 0
  let crashProximityScore = 0
  let minCrashDistance: number | null | undefined = null

  const crashSummary = await fetchCrashSummaryForSegment(segment)

  if (crashSummary) {
    crashCount = crashSummary.close_crash_count ?? 0
    minCrashDistance = crashSummary.min_distance_meters

    if (crashCount > 0) {
      const proximityWeight = Math.max(
        0,
        Math.min(
          1,
          minCrashDistance != null ? (DEFAULT_CRASH_THRESHOLD_METERS - minCrashDistance) / DEFAULT_CRASH_THRESHOLD_METERS : 0.5
        )
      )

      crashProximityScore = Math.min(crashCount * 6 * proximityWeight + crashCount * 2, 25)
      rawScore += crashProximityScore
    }
  }

  return {
    score: Math.round(Math.min(rawScore, 100)),
    leftTurnRisk,
    crashCount,
    crashProximityScore,
    minCrashDistance: minCrashDistance ?? null
  }
}

type PrimeOptions = {
  thresholdMeters?: number
  maxCrashesPerSegment?: number
}

export async function primeCrashSummariesForSegments(
  segments: StepperSegmentInfo[],
  options?: PrimeOptions
): Promise<void> {
  const threshold = options?.thresholdMeters ?? DEFAULT_CRASH_THRESHOLD_METERS
  const maxCrashes = options?.maxCrashesPerSegment ?? 5

  const segmentsToFetch = segments.filter((segment): segment is StepperSegmentInfo & { coordinates: [number, number][] } => {
    if (!segment.coordinates || segment.coordinates.length < 2) {
      return false
    }

    const cacheKey = getSegmentCacheKey(segment)
    return !crashSummaryCache.has(cacheKey)
  })

  if (segmentsToFetch.length === 0) {
    return
  }

  const payloadSegments = segmentsToFetch.map((segment) => ({
    leg_index: segment.leg_index,
    step_index: segment.step_index,
    coordinates: segment.coordinates,
    distance_meters: segment.distance_meters,
    duration_seconds: segment.duration_seconds,
    duration_in_traffic_seconds: segment.duration_in_traffic_seconds,
    instruction: segment.instruction,
    travel_mode: segment.travel_mode
  }))

  try {
    const response = await apiService.analyzeCrashProximity({
      segments: payloadSegments,
      threshold_meters: threshold,
      max_crashes_per_segment: maxCrashes
    })

    if (response && response.success && Array.isArray(response.segments)) {
      segmentsToFetch.forEach((segment, index) => {
        const cacheKey = getSegmentCacheKey(segment)
        const segmentSummary = response.segments?.[index]
        const summary: CrashProximitySummary | null = segmentSummary
          ? {
              close_crash_count: segmentSummary.close_crash_count ?? 0,
              min_distance_meters: segmentSummary.min_distance_meters ?? null
            }
          : null
        crashSummaryCache.set(cacheKey, Promise.resolve(summary))
      })
    } else {
      segmentsToFetch.forEach((segment) => {
        crashSummaryCache.set(getSegmentCacheKey(segment), Promise.resolve(null))
      })
    }
  } catch (error) {
    console.error("Failed to prime crash proximity summaries", error)
    segmentsToFetch.forEach((segment) => {
      crashSummaryCache.set(getSegmentCacheKey(segment), Promise.resolve(null))
    })
  }
}

export function Stepper({ children, className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex flex-col gap-10", className)} {...props}>
      {children}
    </div>
  )
}

export function StepperItem({ 
  children, 
  className,
  step,
  segmentInfo,
  segmentRisk,
  totalRisk,
  ...props 
}: React.HTMLAttributes<HTMLDivElement> & { step: number; segmentInfo?: StepperSegmentInfo; segmentRisk?: SegmentRiskScore | null; totalRisk?: number }) {
  const context = React.useContext(StepperContext)
  const currentStep = context?.currentStep ?? 1
  void segmentInfo;
  
  const state = step < currentStep ? "completed" : step === currentStep ? "5" : "0"
  const riskScore = typeof totalRisk === "number" ? totalRisk : segmentRisk?.score ?? null
  const crashCount = segmentRisk?.crashCount ?? 0
  const showCrashBadge = crashCount > 0
  
  return (
    <div className={cn("relative flex w-full items-start gap-6 group", className)} data-state={state} {...props}>
      {children}
      {typeof riskScore === "number" && (
        <Alert className="absolute top-0 right-0 w-32 px-2.5 py-1.5 border-red-200 bg-red-50">
          <AlertDescription>Risk: {riskScore}</AlertDescription>
        </Alert>
      )}
      {showCrashBadge && (
        <div className="absolute top-9 right-0 inline-flex items-center gap-1 rounded border border-amber-200 bg-amber-50 px-1.5 py-1 text-[10px] font-medium text-amber-700">
          {crashCount} incident{crashCount === 1 ? "" : "s"}
        </div>
      )}
    </div>
  )
}

export function StepperSeparator({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("absolute left-[18px] top-[38px] block h-[105%] w-0.5 shrink-0 rounded-full bg-muted group-data-[state=completed]:bg-primary", className)} {...props} />
}

export function StepperTrigger({ children, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={cn("z-10", className)} {...props}>{children}</button>
}

export function StepperTitle({ children, className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-sm font-semibold transition lg:text-base", className)} {...props}>{children}</h3>
}

export function StepperDescription({ children, className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-xs text-muted-foreground transition md:block lg:text-sm", className)} {...props}>{children}</p>
}