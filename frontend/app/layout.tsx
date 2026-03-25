import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import SuperUserProvider from "@/components/SuperUserProvider";
import HeaderTitle from "@/components/HeaderTitle";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Grades",
  description: "SIS assignment tracker with daily snapshots and change detection",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <SuperUserProvider>
          <div className="min-h-screen bg-white dark:bg-gray-950">
            <header className="border-b border-gray-200 dark:border-gray-800 px-6 py-3">
              <HeaderTitle />
            </header>
            <main className="p-6">{children}</main>
          </div>
        </SuperUserProvider>
      </body>
    </html>
  );
}
