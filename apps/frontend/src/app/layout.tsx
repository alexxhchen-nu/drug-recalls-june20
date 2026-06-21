import type { Metadata } from "next";
import { Bricolage_Grotesque, Patrick_Hand } from "next/font/google";
import "./globals.css";

const bricolage = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
});

const patrick = Patrick_Hand({
  variable: "--font-patrick",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "FDA Animal Safety Search",
  description:
    "A comic-inspired search interface for FDA animal and veterinary safety records.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${bricolage.variable} ${patrick.variable}`}>
        {children}
      </body>
    </html>
  );
}
