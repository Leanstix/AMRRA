import { DM_Sans } from "next/font/google"
import "./globals.css"
import { SettingsProvider } from "@/components/shared/settings-context"

const dmSans = DM_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-dm-sans",
})

export const metadata = {
  title: "AI Research Reproducibility Copilot",
  description: "Extract hypotheses, generate experiment plans, and create reproducibility reports from ML papers",
  generator: "v0.app",
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${dmSans.variable} antialiased`}>
      <body className="font-serif">
        <SettingsProvider>{children}</SettingsProvider>
      </body>
    </html>
  )
}
