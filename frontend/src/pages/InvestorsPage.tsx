import { useMemo } from "react";
import { BigPill, MegaPill, VideoTop } from "@/components/shared";

/* -------------------- Investors -------------------- */
export default function InvestorsPage() {
  const market = useMemo(
    () => [
      <>US Class 7–8 trucks: <b>3M</b>.</>,
      <>World: <b>~15–20M</b> trucks.</>,
      <>TAM <b>$12B/yr</b> • SAM <b>$1.8B/yr</b>.</>,
    ],
    []
  );

  const unitEcon = useMemo(
    () => [
      <>Gross margin ≈ <b>90%</b>.</>,
      <>LTV <b>$2,700</b> / truck.</>,
      <>CAC <b>$300</b> / truck.</>,
      <>LTV:CAC <b>9:1</b>.</>,
    ],
    []
  );

  return (
    <div className="space-y-8">
      {/* Investors video */}
      <VideoTop url="https://youtu.be/JpqvdIRZcV8?si=8s5sOts76aw5rXZX" />

      <MegaPill title="Market">
        {market.map((x, i) => (
          <BigPill key={i}>{x}</BigPill>
        ))}
      </MegaPill>

      <MegaPill title="Unit Econ">
        {unitEcon.map((x, i) => (
          <BigPill key={i}>{x}</BigPill>
        ))}
      </MegaPill>
    </div>
  );
}