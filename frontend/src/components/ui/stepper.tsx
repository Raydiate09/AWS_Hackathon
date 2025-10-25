import * as React from "react"
import { cn } from "@/lib/utils"

interface StepperContextValue {
  currentStep: number
  setCurrentStep: (step: number) => void
}

const StepperContext = React.createContext<StepperContextValue | undefined>(undefined)

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
  ...props 
}: React.HTMLAttributes<HTMLDivElement> & { step: number }) {
  const context = React.useContext(StepperContext)
  const currentStep = context?.currentStep ?? 1
  
  const state = step < currentStep ? "completed" : step === currentStep ? "active" : "inactive"
  
  return (
    <div className={cn("relative flex w-full items-start gap-6 group", className)} data-state={state} {...props}>
      {children}
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