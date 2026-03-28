import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Contract Shield - AI Contract Risk Analysis",
  description: "AI-powered contract risk analysis for freelancers. Upload PDF/DOCX contracts to identify risks, get negotiation tips, and generate response emails.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
