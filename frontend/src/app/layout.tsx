import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NarrativeIQ | Narrative Intelligence Platform",
  description: "Global Event and Narrative Intelligence Platform for Data Warehousing and Big Data.",
  icons: {
    icon: "/logos/narrativeiq-icon.png",
  }
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
