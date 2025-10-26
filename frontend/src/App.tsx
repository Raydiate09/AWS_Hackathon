import './App.css'
import { Calendar } from "@/components/ui/calendar";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import type { DateRange } from "react-day-picker";
import { Check, Circle, Dot } from "lucide-react";
import { 
  Stepper, 
  StepperItem, 
  StepperSeparator, 
  StepperTrigger, 
  StepperTitle, 
  StepperDescription 
} from "@/components/ui/stepper";
import MapboxExample from "@/components/MapboxExample";

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

function ButtonDemo() {
  return <Button>Click me</Button>;
}

function StepperDemo() {
  const [currentStep, setCurrentStep] = useState(1);

  const steps = [
    {
      step: 1,
      title: "Pickup at SFO",
      description: "Package collected from San Francisco International Airport cargo terminal",
    },
    {
      step: 2,
      title: "Depart SFO Area",
      description: "Leaving airport grounds and entering Highway 101 northbound",
    },
    {
      step: 3,
      title: "San Mateo to Palo Alto",
      description: "Traveling through San Mateo and Palo Alto areas via US-101",
    },
    {
      step: 4,
      title: "Mountain View Transit",
      description: "Passing through Mountain View and Sunnyvale on route to Santa Clara",
    },
    {
      step: 5,
      title: "Delivery at SCU",
      description: "Final destination reached at Santa Clara University campus",
    },
  ];

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

          return (
            <StepperItem key={step.step} step={step.step}>
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
                <StepperTitle
                  className={state === "active" ? "text-primary" : ""}
                >
                  {step.title}
                </StepperTitle>
                <StepperDescription
                  className={state === "active" ? "text-primary" : ""}
                >
                  {step.description}
                </StepperDescription>
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
  return (
    <div className="landing-page">
      <h1>DTS</h1>
      <ButtonDemo />
      <CalendarRangeDemo />
      <StepperDemo />
      <CrashDataDemo />
      <div style={{ height: '500px', width: '100%' }}>
        <MapboxExample />
      </div>
    </div>
  )
}

export default App