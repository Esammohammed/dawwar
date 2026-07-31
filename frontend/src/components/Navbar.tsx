import React, { useState } from 'react';
import { Link, useNavigate } from 'react me-auto';
import { Link as RouterLink } from 'react-router-dom';
import { Home, Building2, Newspaper, PlusCircle, User as UserIcon, LogOut, Phone } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import AuthModal from './AuthModal';

const Navbar: React.FC = () => {
  const { user, logout } = useAuthStore();
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-200/80 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            
            {/* Brand Logo */}
            <RouterLink to="/" className="flex items-center gap-2 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform">
                <Building2 className="w-6 h-6" />
              </div>
              <div className="flex flex-col">
                <span className="text-2xl font-extrabold bg-gradient-to-r from-sky-700 via-sky-600 to-indigo-700 bg-clip-text text-transparent tracking-tight">
                  دوّار
                </span>
                <span className="text-[10px] text-slate-500 font-medium -mt-1">
                  عقارات وفرص مصر
                </span>
              </div>
            </RouterLink>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-1 font-medium text-slate-700">
              <RouterLink to="/" className="px-3 py-2 rounded-lg hover:bg-slate-100/80 hover:text-sky-600 transition-colors flex items-center gap-1.5">
                <Home className="w-4 h-4" />
                الرئيسية
              </RouterLink>
              <RouterLink to="/listings" className="px-3 py-2 rounded-lg hover:bg-slate-100/80 hover:text-sky-600 transition-colors flex items-center gap-1.5">
                <Building2 className="w-4 h-4" />
                تصفح العقارات
              </RouterLink>
              <RouterLink to="/projects" className="px-3 py-2 rounded-lg hover:bg-slate-100/80 hover:text-sky-600 transition-colors flex items-center gap-1.5">
                المشروعات السكنية
              </RouterLink>
              <RouterLink to="/gov-news" className="px-3 py-2 rounded-lg hover:bg-slate-100/80 hover:text-sky-600 transition-colors flex items-center gap-1.5">
                <Newspaper className="w-4 h-4" />
                الإعلانات الحكومية
              </RouterLink>
            </nav>

            {/* Right Action Controls */}
            <div className="flex items-center gap-3">
              <RouterLink
                to="/sell"
                className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-md shadow-amber-500/20 hover:from-amber-600 hover:to-amber-700 transition-all active:scale-95"
              >
                <PlusCircle className="w-4 h-4" />
                أضف وحدتك للبيع
              </RouterLink>

              {user ? (
                <div className="flex items-center gap-2">
                  <RouterLink
                    to="/account"
                    className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-sm font-semibold transition-colors"
                  >
                    <UserIcon className="w-4 h-4 text-sky-600" />
                    <span>{user.full_name || user.phone}</span>
                  </RouterLink>
                  <button
                    onClick={logout}
                    title="تسجيل الخروج"
                    className="p-2 rounded-xl text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsAuthOpen(true)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-xl bg-sky-600 text-white hover:bg-sky-700 transition-colors shadow-sm"
                >
                  <Phone className="w-4 h-4" />
                  دخول / تسجيل
                </button>
              )}
            </div>

          </div>
        </div>
      </header>

      {isAuthOpen && <AuthModal onClose={() => setIsAuthOpen(false)} />}
    </>
  );
};

export default Navbar;
