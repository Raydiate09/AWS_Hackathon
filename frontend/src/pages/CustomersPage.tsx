import { useMemo } from "react";
import { BigPill, MegaPill, VideoTop } from "@/components/shared";

/* -------------------- Customers (Why DTS) -------------------- */
export default function CustomersPage() {
  const hardFacts = useMemo(
    () => [
      <>Left turns: <b>3×</b> deaths.</>,
      <>Curves: <b>4×</b> crash rate.</>,
      <>Rain: <b>+34%</b> fatal risk.</>,
      <>Bright sun: <b>+16%</b> life-threatening risk.</>,
      <>Injury crash: <b>$383k</b>.</>,
      <>Fatal crash: <b>$14M</b>.</>,
    ],
    []
  );

  const weSee = useMemo(
    () => [
      <>Historic <b>crash hotspots</b>.</>,
      <>Live <b>traffic density</b> (OpenCV).</>,
      <><b>Left-turn</b> danger zones.</>,
      <><b>Sunset glare</b> timing.</>,
      <><b>Storm paths</b> + wet roads.</>,
    ],
    []
  );

  return (
    <div className="space-y-8">
      {/* Top video */}
      <VideoTop url="https://youtu.be/OtBR2T2WJ3Q?si=Sh8auvKhHMa7g0io" />

      {/* Huge centered heading (no pill) */}
      <h1 className="text-center text-4xl md:text-6xl font-semibold leading-tight">
        Mapping Apps Don&apos;t Understand Trucks. <span className="text-primary">We Do.</span>
      </h1>

      <MegaPill title="Facts">
        {hardFacts.map((x, i) => (
          <BigPill key={i}>{x}</BigPill>
        ))}
      </MegaPill>

      <MegaPill title="See">
        {weSee.map((x, i) => (
          <BigPill key={i}>{x}</BigPill>
        ))}
      </MegaPill>

      {/* ROI heading + bottom video */}
      <h2 className="text-center text-4xl md:text-6xl font-semibold leading-tight">
        <span className="text-primary">12X</span> ROI
      </h2>
      <VideoTop url="https://youtu.be/QIqOPfZ969Y?si=HMzRkNXPIyAwBr6b" />
    </div>
  );
}