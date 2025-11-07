'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ThemeToggle from './theme-toggle';
import GradientButton from './gradient-button';
import { Menu, X, Sparkles } from 'lucide-react';

interface NavbarProps {
  variant?: 'landing' | 'app';
}

export default function Navbar({ variant = 'landing' }: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/30 border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 text-xl font-bold hover:opacity-80 transition-opacity"
          >
            <Sparkles className="w-6 h-6 text-primary" />
            <span className="gradient-text">EduSynth</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {variant === 'app' && (
              <>
                <Link
                  href="/dashboard"
                  className={`text-sm font-medium transition-colors ${
                    isActive('/dashboard')
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Dashboard
                </Link>
                <Link
                  href="/generator"
                  className={`text-sm font-medium transition-colors ${
                    isActive('/generator')
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Create Lecture
                </Link>
              </>
            )}

            <ThemeToggle />

            {variant === 'landing' && (
              <div className="flex items-center gap-3">
                <button className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                  Login
                </button>
                <GradientButton size="sm">Sign Up</GradientButton>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center gap-3">
            <ThemeToggle />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-foreground hover:text-primary transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-white/10 backdrop-blur-xl bg-black/40">
          <div className="px-4 py-6 space-y-4">
            {variant === 'app' && (
              <>
                <Link
                  href="/dashboard"
                  className={`block text-base font-medium transition-colors ${
                    isActive('/dashboard')
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Dashboard
                </Link>
                <Link
                  href="/generator"
                  className={`block text-base font-medium transition-colors ${
                    isActive('/generator')
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Create Lecture
                </Link>
              </>
            )}

            {variant === 'landing' && (
              <div className="space-y-3 pt-4 border-t border-white/10">
                <button className="block w-full text-left text-base font-medium text-muted-foreground hover:text-foreground transition-colors">
                  Login
                </button>
                <GradientButton className="w-full">Sign Up</GradientButton>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
