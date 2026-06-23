'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
  href: string;
  label: string;
}

export default function RootLayoutClient({
  children,
  navItems,
}: {
  children: React.ReactNode;
  navItems: NavItem[];
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  const close = useCallback(() => setMobileOpen(false), []);

  useEffect(() => { close(); }, [pathname, close]);

  useEffect(() => {
    if (!mobileOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [mobileOpen, close]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-surface-warm/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto flex items-center gap-4 px-4 py-3">
          {/* Logo */}
          <Link href="/arbitlens" className="flex items-center gap-2.5 group" onClick={close}>
            <div className="w-8 h-8 rounded-lg bg-ink text-white text-sm font-bold flex items-center justify-center transition-transform group-hover:scale-105">
              A
            </div>
            <span className="text-sm font-semibold text-ink tracking-tight hidden sm:block">
              ArbitLens
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="ml-auto hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || 
                (item.href !== '/arbitlens' && pathname.startsWith(item.href.split('?')[0]));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-ink text-white'
                      : 'text-ink-muted hover:text-ink hover:bg-surface-warm'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen((v) => !v)}
            className="ml-auto md:hidden w-9 h-9 flex items-center justify-center rounded-lg hover:bg-surface-warm transition-colors"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            <div className="flex flex-col gap-1">
              <span className={`block h-0.5 w-5 rounded-full bg-ink transition-all duration-200 ${mobileOpen ? 'translate-y-1 rotate-45' : ''}`} />
              <span className={`block h-0.5 w-5 rounded-full bg-ink transition-all duration-200 ${mobileOpen ? 'opacity-0' : ''}`} />
              <span className={`block h-0.5 w-5 rounded-full bg-ink transition-all duration-200 ${mobileOpen ? '-translate-y-1.5 -rotate-45' : ''}`} />
            </div>
          </button>
        </div>

        {/* Mobile menu */}
        <div className={`md:hidden overflow-hidden border-t border-border transition-all duration-200 ${mobileOpen ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'}`}>
          <nav className="px-4 py-3">
            {navItems.map((item) => {
              const isActive = pathname === item.href || 
                (item.href !== '/arbitlens' && pathname.startsWith(item.href.split('?')[0]));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={close}
                  className={`block px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-ink text-white'
                      : 'text-ink-muted hover:text-ink hover:bg-surface-warm'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6 sm:px-6 sm:py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-surface-warm">
        <div className="max-w-6xl mx-auto px-4 py-6 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-ink text-white text-xs font-bold flex items-center justify-center">
                A
              </div>
              <span className="text-xs text-ink-muted">
                ArbitLens — Cross-Marketplace Intelligence
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-ink-faint">
              <span>13,508 products</span>
              <span className="text-border-soft">|</span>
              <span>5 platforms</span>
              <span className="text-border-soft">|</span>
              <span>1,441 matches</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
