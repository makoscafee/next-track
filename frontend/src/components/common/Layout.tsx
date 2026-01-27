import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { Music, Home, BarChart3, Settings } from "lucide-react";

interface LayoutProps {
  children: ReactNode;
  showNav?: boolean;
}

export default function Layout({ children, showNav = true }: LayoutProps) {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith("/admin");

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {showNav && (
        <nav className="glass sticky top-0 z-50 border-b border-white/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl gradient-bg flex items-center justify-center">
                  <Music className="w-6 h-6 text-white" />
                </div>
                <span className="text-xl font-bold gradient-text">
                  NextTrack
                </span>
              </Link>

              <div className="flex items-center gap-6">
                {!isAdmin ? (
                  <>
                    <Link
                      to="/"
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                        location.pathname === "/"
                          ? "bg-[var(--primary)]/20 text-[var(--primary)]"
                          : "text-[var(--text-muted)] hover:text-white"
                      }`}
                    >
                      <Home className="w-4 h-4" />
                      <span>Home</span>
                    </Link>
                    <Link
                      to="/admin"
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-[var(--text-muted)] hover:text-white transition-colors"
                    >
                      <Settings className="w-4 h-4" />
                      <span>Admin</span>
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      to="/admin"
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                        location.pathname === "/admin"
                          ? "bg-[var(--primary)]/20 text-[var(--primary)]"
                          : "text-[var(--text-muted)] hover:text-white"
                      }`}
                    >
                      <BarChart3 className="w-4 h-4" />
                      <span>Dashboard</span>
                    </Link>
                    <Link
                      to="/admin/experiments"
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                        location.pathname === "/admin/experiments"
                          ? "bg-[var(--primary)]/20 text-[var(--primary)]"
                          : "text-[var(--text-muted)] hover:text-white"
                      }`}
                    >
                      <Settings className="w-4 h-4" />
                      <span>Experiments</span>
                    </Link>
                    <Link
                      to="/"
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-[var(--text-muted)] hover:text-white transition-colors"
                    >
                      <Home className="w-4 h-4" />
                      <span>User View</span>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        </nav>
      )}

      <main>{children}</main>
    </div>
  );
}
