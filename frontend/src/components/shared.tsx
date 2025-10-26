// src/components/shared.tsx
import React from "react";

function toYouTubeEmbed(url: string) {
  try {
    const u = new URL(url);
    let id = "";
    if (u.hostname.includes("youtu.be")) {
      id = u.pathname.split("/")[1] || "";
    } else if (u.pathname.startsWith("/shorts/")) {
      id = u.pathname.split("/")[2] || "";
    } else if (u.pathname.startsWith("/embed/")) {
      id = u.pathname.split("/")[2] || "";
    } else if (u.searchParams.get("v")) {
      id = u.searchParams.get("v") || "";
    }
    if (!id) return url.replace("watch?v=", "embed/");
    const start = u.searchParams.get("t") || u.searchParams.get("start");
    const qs = new URLSearchParams();
    if (start) qs.set("start", start.replace("s", ""));
    return `https://www.youtube.com/embed/${id}${qs.toString() ? `?${qs.toString()}` : ""}`;
  } catch {
    return url.replace("watch?v=", "embed/");
  }
}

export function VideoTop({ url }: { url: string }) {
  const embed = toYouTubeEmbed(url);
  return (
    <div className="rounded-2xl border overflow-hidden">
      <div className="aspect-video">
        <iframe
          className="h-full w-full"
          src={embed}
          title="demo video"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        />
      </div>
    </div>
  );
}

export function BigPill({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-full border bg-card px-6 py-8 md:px-10 md:py-12 shadow-sm w-full max-w-3xl mx-auto">
      <div className="break-words text-2xl md:text-4xl leading-tight">
        {children}
      </div>
    </div>
  );
}

export function MegaPill({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[40px] border bg-card px-6 py-8 md:px-10 md:py-12 shadow-sm">
      <h2 className="text-3xl md:text-5xl font-semibold mb-6 text-center">{title}</h2>
      <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-2 place-items-center">
        {children}
      </div>
    </section>
  );
}
