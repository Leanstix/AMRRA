import { DM_Sans } from "next/font/google"
import "./globals.css"
import { SettingsProvider } from "@/components/shared/settings-context"

const dmSans = DM_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-dm-sans",
})

export const metadata = {
  title: "AMRRA — Agentic Research Workbench",
  description: "Evidence-grounded agentic research with deterministic statistical validation.",
  generator: "AMRRA",
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${dmSans.variable} antialiased`}>
      <body className="font-sans">
        <SettingsProvider>{children}</SettingsProvider>
      </body>
    </html>
  )
}
