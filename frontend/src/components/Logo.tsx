import clsx from "clsx";

interface LogoProps {
  variant: "full" | "nav" | "icon" | "report";
  className?: string;
}

export function Logo({ variant, className }: LogoProps) {
  if (variant === "full" || variant === "report") {
    return (
      <img
        className={clsx("logo logo-full", variant === "report" && "logo-report", className)}
        src="/logos/narrativeiq-full.png"
        alt="NarrativeIQ full logo"
      />
    );
  }

  if (variant === "nav") {
    return (
      <div className={clsx("logo-nav", className)} aria-label="NarrativeIQ">
        <img className="logo-icon" src="/logos/narrativeiq-icon.png" alt="" />
        <span>NarrativeIQ</span>
      </div>
    );
  }

  return (
    <img
      className={clsx("logo-icon-only", className)}
      src="/logos/narrativeiq-icon.png"
      alt="NarrativeIQ icon"
    />
  );
}
