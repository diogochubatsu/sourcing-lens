import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ArbitLens — Cross-Marketplace Product Intelligence',
  description: 'Search products across Chinese marketplaces. Visual matching, price comparison, and sourcing intelligence.',
  themeColor: '#FAFAF9',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#FAFAF9',
  viewportFit: 'cover',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" />
      </head>
      <body className="min-h-screen bg-[#FAFAF9] text-[#0A0A0A] antialiased" style={{ fontFamily: "'Inter', sans-serif" }}>
        <header className="sticky top-0 z-50 bg-[#FAFAF9]/80 backdrop-blur-xl border-b border-[#E5E5E5]">
          <div className="max-w-6xl mx-auto flex items-center justify-between px-4 h-12">
            <a href="/arbitlens" className="flex items-center gap-2">
              <div className="w-7 h-7 bg-[#0A0A0A] rounded-md flex items-center justify-center text-white text-xs font-bold">A</div>
              <span className="text-sm font-semibold hidden sm:block">ArbitLens</span>
            </a>
            <nav className="flex items-center gap-1">
              <a href="/arbitlens" className="px-2.5 py-1.5 text-xs font-medium text-[#525252] hover:text-[#0A0A0A] rounded-md hover:bg-[#F5F5F5] transition-colors">Dashboard</a>
              <a href="/arbitlens/explore" className="px-2.5 py-1.5 text-xs font-medium text-[#525252] hover:text-[#0A0A0A] rounded-md hover:bg-[#F5F5F5] transition-colors">Explore</a>
              <a href="/arbitlens/categories" className="px-2.5 py-1.5 text-xs font-medium text-[#525252] hover:text-[#0A0A0A] rounded-md hover:bg-[#F5F5F5] transition-colors">Categories</a>
              <a href="/arbitlens/matches" className="px-2.5 py-1.5 text-xs font-medium text-[#525252] hover:text-[#0A0A0A] rounded-md hover:bg-[#F5F5F5] transition-colors">Matches</a>
              <a href="/arbitlens/clusters" className="px-2.5 py-1.5 text-xs font-medium text-[#525252] hover:text-[#0A0A0A] rounded-md hover:bg-[#F5F5F5] transition-colors">Clusters</a>
            </nav>
          </div>
        </header>
        <main>{children}</main>
        <footer className="border-t border-[#E5E5E5] bg-white mt-12">
          <div className="max-w-6xl mx-auto px-4 py-6 flex items-center justify-between text-[10px] text-[#8A8A8A]">
            <span>ArbitLens — Cross-Marketplace Intelligence</span>
            <span>13,508 products · 5 platforms · 1,441 matches</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
