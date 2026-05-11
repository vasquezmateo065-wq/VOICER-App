import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VOICER — Text to Speech Premium",
  description: "Generador de audio de voz con IA. Sistema de bloques dinámicos con voces neurales de alta calidad.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <div className="ambient-bg" aria-hidden="true" />
        <div className="relative z-10 min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
