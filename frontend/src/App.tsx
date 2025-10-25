import './App.css'
import { Calendar } from "@/components/ui/calendar";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import type { DateRange } from "react-day-picker";

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

function App() {
  return (
    <div className="landing-page">
      <h1>Welcome to Our Landing Page</h1>
      <ButtonDemo />
      <CalendarRangeDemo />
    </div>
  )
}

export default App