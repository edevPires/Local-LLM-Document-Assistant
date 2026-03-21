"use client";

import dynamic from "next/dynamic";

const ASCIIText = dynamic(() => import("@/components/ASCIIText"), {
  ssr: false,
});

export default function ShowcasePage() {
  return (
    <div
      className="h-screen flex flex-col items-center justify-center font-mono"
      style={{ background: "#0c0c0c" }}
    >
      <div className="relative w-full" style={{ height: "40vh" }}>
        <ASCIIText
          text="Resume AI"
          asciiFontSize={5}
          enableWaves
          textColor="#fdf9f3"
          planeBaseHeight={7}
        />
      </div>

      <p className="text-base pb-10 tracking-wide" style={{ color: "#555" }}>
        Bruno Mendes Pires · 2026
      </p>
    </div>
  );
}
