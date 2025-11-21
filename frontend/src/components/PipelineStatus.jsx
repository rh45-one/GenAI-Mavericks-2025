import React, { useMemo, useEffect, useState } from "react";

const AnimatedText = ({ text }) => {
  const [dots, setDots] = useState("");
  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 400);
    return () => clearInterval(interval);
  }, []);
  return (
    <span>
      {text}
      <span className="animated-dots">{dots}</span>
    </span>
  );
};

export function PipelineStatus({ steps, currentStepIndex, status }) {
  const normalizedSteps = useMemo(() => steps || [], [steps]);
  if (!normalizedSteps.length || status === "idle") {
    return null;
  }

  return (
    <div className="pipeline-status">
      <h3>Estado del proceso</h3>
      <ol>
        {normalizedSteps.map((step, index) => {
          const isActive = index === currentStepIndex;
          const isDone = index < currentStepIndex;
          return (
            <li key={step} className={isDone ? "done" : isActive ? "active" : "pending"}>
              {isDone ? "✔ " : isActive ? <AnimatedText text={step} /> : step}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
