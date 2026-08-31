import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Home, Building2, Newspaper, FolderKanban, PlusCircle, User, LogOut, Phone, Moon, Sun, Menu, X } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useThemeStore } from '../stores/themeStore';
import { useTranslation } from '../i18n/i18nContext';
import LanguageSwitcher from './LanguageSwitcher';
import AuthModal from './AuthModal';
import styles from './Navbar.module.css';

const Navbar = () => {
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const { t } = useTranslation();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const closeDrawer = () => setIsDrawerOpen(false);

  return (
    <>
      <header className={styles.header}>
        <div className={styles.container}>

          <Link to="/" className={styles.logo}>
            <img src="/dawwar-mark.svg" alt="Dawwar" className={styles.logoMark} />
            <div className={styles.logoText}>
              <span className={styles.brandName}>{t('nav.brand')}</span>
              <span className={styles.tagline}>{t('nav.tagline')}</span>
            </div>
          </Link>

          {/* Desktop nav links */}
          <nav className={styles.nav}>
            <Link to="/" className={styles.navLink}>
              <Home size={18} />
              {t('nav.home')}
            </Link>
            <Link to="/listings" className={styles.navLink}>
              <Building2 size={18} />
              {t('nav.listings')}
            </Link>
            <Link to="/projects" className={styles.navLink}>
              <FolderKanban size={18} />
              {t('nav.projects')}
            </Link>
            <Link to="/exit" className={styles.navLink}>
              {t('exitDeals.navLink')}
            </Link>
            <Link to="/gov-news" className={styles.navLink}>
              <Newspaper size={18} />
              {t('nav.govNews')}
            </Link>
          </nav>

          {/* Desktop action buttons */}
          <div className={styles.actions}>
            <button
              onClick={toggleTheme}
              className={styles.themeBtn}
              title={theme === 'dark' ? t('nav.lightMode') : t('nav.darkMode')}
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <LanguageSwitcher />

            <Link to="/sell" className={styles.addBtn}>
              <PlusCircle size={18} />
              {t('nav.sellUnit')}
            </Link>

            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Link to="/account" className={styles.userBtn}>
                  <User size={18} style={{ color: 'var(--accent)' }} />
                  <span>{user.full_name || user.phone}</span>
                </Link>
                <button onClick={logout} className={styles.logoutBtn} title={t('nav.logout')}>
                  <LogOut size={18} />
                </button>
              </div>
            ) : (
              <button onClick={() => setIsAuthOpen(true)} className={styles.authBtn}>
                <Phone size={18} />
                {t('nav.login')}
              </button>
            )}
          </div>

          {/* Mobile hamburger */}
          <button className={styles.hamburger} onClick={() => setIsDrawerOpen(true)} aria-label="Open menu">
            <Menu size={22} />
          </button>

        </div>
      </header>

      {/* ---- Mobile Drawer ---- */}
      <div
        className={`${styles.mobileOverlay} ${isDrawerOpen ? styles.open : ''}`}
        onClick={closeDrawer}
      />
      <aside className={`${styles.mobileDrawer} ${isDrawerOpen ? styles.open : ''}`}>
        <button className={styles.drawerClose} onClick={closeDrawer} aria-label="Close menu">
          <X size={20} />
        </button>

        <nav className={styles.drawerNav}>
          <Link to="/" className={styles.drawerNavLink} onClick={closeDrawer}>
            <Home size={20} />
            {t('nav.home')}
          </Link>
          <Link to="/listings" className={styles.drawerNavLink} onClick={closeDrawer}>
            <Building2 size={20} />
            {t('nav.listings')}
          </Link>
          <Link to="/projects" className={styles.drawerNavLink} onClick={closeDrawer}>
            <FolderKanban size={20} />
            {t('nav.projects')}
          </Link>
          <Link to="/gov-news" className={styles.drawerNavLink} onClick={closeDrawer}>
            <Newspaper size={20} />
            {t('nav.govNews')}
          </Link>
        </nav>

        <div className={styles.drawerActions}>
          <Link to="/sell" className={styles.addBtn} onClick={closeDrawer}>
            <PlusCircle size={18} />
            {t('nav.sellUnit')}
          </Link>

          {user ? (
            <>
              <Link to="/account" className={styles.userBtn} onClick={closeDrawer}>
                <User size={18} style={{ color: 'var(--accent)' }} />
                <span>{user.full_name || user.phone}</span>
              </Link>
              <button onClick={() => { logout(); closeDrawer(); }} className={styles.logoutBtn}>
                <LogOut size={18} />
                {t('nav.logout')}
              </button>
            </>
          ) : (
            <button onClick={() => { setIsAuthOpen(true); closeDrawer(); }} className={styles.authBtn}>
              <Phone size={18} />
              {t('nav.login')}
            </button>
          )}

          <div className={styles.drawerRow}>
            <button
              onClick={toggleTheme}
              className={styles.themeBtn}
              title={theme === 'dark' ? t('nav.lightMode') : t('nav.darkMode')}
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <LanguageSwitcher />
          </div>
        </div>
      </aside>

      {isAuthOpen && <AuthModal onClose={() => setIsAuthOpen(false)} />}
    </>
  );
};

export default Navbar;
