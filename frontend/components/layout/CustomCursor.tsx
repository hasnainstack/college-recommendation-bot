"use client";
import { useEffect, useRef } from "react";

export default function CustomCursor() {
  const dotRef   = useRef<HTMLDivElement>(null);
  const ringRef  = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mouseX = 0, mouseY = 0;
    let ringX  = 0, ringY  = 0;
    let raf: number;

    const onMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (dotRef.current) {
        dotRef.current.style.transform = `translate(${mouseX}px, ${mouseY}px)`;
      }
    };

    const animate = () => {
      ringX += (mouseX - ringX) * 0.12;
      ringY += (mouseY - ringY) * 0.12;
      if (ringRef.current) {
        ringRef.current.style.transform = `translate(${ringX}px, ${ringY}px)`;
      }
      raf = requestAnimationFrame(animate);
    };

    const onEnter = (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      if (t.closest("a, button, input, select, textarea, [role='button']")) {
        dotRef.current?.classList.add("cursor-hover");
        ringRef.current?.classList.add("cursor-hover");
      }
    };

    const onLeave = (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      if (t.closest("a, button, input, select, textarea, [role='button']")) {
        dotRef.current?.classList.remove("cursor-hover");
        ringRef.current?.classList.remove("cursor-hover");
      }
    };

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseover", onEnter);
    window.addEventListener("mouseout", onLeave);
    raf = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseover", onEnter);
      window.removeEventListener("mouseout", onLeave);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <>
      <div ref={dotRef}  className="cursor-dot" />
      <div ref={ringRef} className="cursor-ring" />
    </>
  );
}
