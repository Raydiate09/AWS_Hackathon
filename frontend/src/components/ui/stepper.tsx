import * as React from "react"
import { cn } from "@/lib/utils"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { CornerUpLeft } from "lucide-react"

interface StepperContextValue {
  currentStep: number
  setCurrentStep: (step: number) => void
}

const StepperContext = React.createContext<StepperContextValue | undefined>(undefined)

type StepperSegmentInfo = {
  distance_meters?: number
  duration_seconds?: number
  duration_in_traffic_seconds?: number
  travel_mode?: string
  instruction?: string
}

// RISK SCORES, SCORING, WEIGHTING, CONSTANTS
const RISK_SCORE_LEFT_TURN = 10

export function getSegmentRiskScore(segment: StepperSegmentInfo): { score: number | null; leftTurnRisk: boolean } {
  const distanceMeters = segment.distance_meters ?? 0
  const durationSeconds = segment.duration_in_traffic_seconds ?? segment.duration_seconds ?? 0

  if (distanceMeters === 0 && durationSeconds === 0) {
    return { score: null, leftTurnRisk: false }
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

  return { score: Math.round(Math.min(rawScore, 100)), leftTurnRisk }
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
  totalRisk,
  ...props 
}: React.HTMLAttributes<HTMLDivElement> & { step: number; segmentInfo?: StepperSegmentInfo; totalRisk?: number }) {
  const context = React.useContext(StepperContext)
  const currentStep = context?.currentStep ?? 1
  
  const state = step < currentStep ? "completed" : step === currentStep ? "5" : "0"
  const riskData = segmentInfo ? getSegmentRiskScore(segmentInfo) : null
  const riskScore = totalRisk ?? null
  const leftTurnRisk = riskData?.leftTurnRisk ?? false
  
  return (
    <div className={cn("relative flex w-full items-start gap-6 group", className)} data-state={state} {...props}>
      {children}
      {typeof riskScore === "number" && (
        <Alert className="absolute top-0 right-0 w-32 px-2.5 py-1.5 border-red-200 bg-red-50">
          <AlertDescription>Risk: {riskScore}</AlertDescription>
        </Alert>
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