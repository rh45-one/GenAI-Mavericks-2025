import React from "react";

export function SimplifiedTextPanelPlaceholder({ text, isLoading }) {
  if (isLoading) {
    return <p>Processing document…</p>;
  }

  return <p>{text}</p>;
}
