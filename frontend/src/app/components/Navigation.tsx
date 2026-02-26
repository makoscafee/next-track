import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router';
import { Button } from './ui/button';
import { Music2, Menu, X, LayoutDashboard, LogOut } from 'lucide-react';
import { isLoggedIn, clearToken } from '../../services/adminApi';

export function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [adminLoggedIn, setAdminLoggedIn] = useState(isLoggedIn());
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;
  const onAdminPage = location.pathname === '/admin';

  // Re-check login state whenever the admin auth token changes
  useEffect(() => {
    const handler = () => setAdminLoggedIn(isLoggedIn());
    window.addEventListener('admin-auth-change', handler);
    return () => window.removeEventListener('admin-auth-change', handler);
  }, []);

  const handleSignOut = () => {
    clearToken();
    setMobileMenuOpen(false);
  };

  const navLinkClass = (path: string) =>
    `text-sm font-medium transition-colors hover:text-primary ${
      isActive(path) ? 'text-primary' : 'text-muted-foreground'
    }`;

  return (
    <nav className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 font-bold text-lg">
            <Music2 className="w-6 h-6 text-primary" />
            <span>NextTrack</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            <Link to="/demo" className={navLinkClass('/demo')}>Demo</Link>
            <Link
              to="/admin"
              className={`flex items-center gap-1 ${navLinkClass('/admin')}`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              Admin
            </Link>
          </div>

          {/* Right side: Sign Out when admin is logged in, nothing otherwise */}
          <div className="hidden md:flex items-center">
            {onAdminPage && adminLoggedIn ? (
              <Button variant="outline" size="sm" onClick={handleSignOut}>
                <LogOut className="w-3.5 h-3.5 mr-1.5" />
                Sign Out
              </Button>
            ) : null}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 space-y-1 border-t">
            <Link
              to="/demo"
              className={`block py-2 px-1 ${navLinkClass('/demo')}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Demo
            </Link>
            <Link
              to="/admin"
              className={`flex items-center gap-1.5 py-2 px-1 ${navLinkClass('/admin')}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              Admin
            </Link>
            {onAdminPage && adminLoggedIn && (
              <div className="pt-3 border-t mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={handleSignOut}
                >
                  <LogOut className="w-3.5 h-3.5 mr-1.5" />
                  Sign Out
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
