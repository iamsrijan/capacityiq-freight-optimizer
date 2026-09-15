import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CapacityIQ | Multimodal Freight Optimiser',
  description:
    'AI-powered freight and airport retail optimisation for monetising existing capacity.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
