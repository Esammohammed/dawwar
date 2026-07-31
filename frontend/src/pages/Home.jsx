import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Newspaper } from 'lucide-react';
import api from '../api/client';
import ListingCard from '../components/ListingCard';
import FilterBar from '../components/FilterBar';
import { useTranslation } from '../i18n/i18nContext';
import styles from './Home.module.css';

const Home = () => {
  const { t } = useTranslation();
  const [listings, setListings] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [listingsRes, annRes] = await Promise.all([
          api.get('/listings/'),
          api.get('/announcements/')
        ]);
        setListings(listingsRes.data.results || listingsRes.data || []);
        setAnnouncements(annRes.data.results || annRes.data || []);
      } catch (err) {
        console.error('Failed to fetch home data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSearch = () => {
    navigate('/listings');
  };

  return (
    <div>
      {/* Hero Section */}
      <section className={styles.hero}>
        <img src="/dawwar-mark.svg" alt="" className={styles.heroMark} />
        <img src="/dawwar-mark.svg" alt="" className={styles.heroMarkSmall} />
        <div className={styles.heroContent}>
          <div className={styles.badge}>
            <Sparkles size={16} />
            <span>{t('hero.badge')}</span>
          </div>

          <h1 className={styles.heroTitle}>
            {t('hero.title')} <br />
            <span className={styles.highlight}>{t('hero.highlight')}</span>
          </h1>

          <p className={styles.heroSubtitle}>
            {t('hero.subtitle')}
          </p>

          <FilterBar onSearch={handleSearch} />
        </div>
      </section>

      {/* Featured Listings */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <h2 className={styles.sectionTitle}>{t('listings.title')}</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{t('listings.subtitle')}</p>
          </div>
          <Link to="/listings" className={styles.viewAll}>
            {t('listings.details')} →
          </Link>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>{t('listings.loading')}</div>
        ) : listings.length > 0 ? (
          <div className={styles.grid}>
            {listings.slice(0, 6).map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>{t('listings.noResults')}</div>
        )}
      </section>

      {/* Gov News Section */}
      <section className={styles.section} style={{ background: 'var(--surface-subtle)', padding: '3rem 1.5rem', borderRadius: '24px' }}>
        <div className={styles.sectionHeader}>
          <div>
            <h2 className={styles.sectionTitle} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Newspaper style={{ color: 'var(--accent)' }} />
              {t('govNews.title')}
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{t('govNews.subtitle')}</p>
          </div>
          <Link to="/gov-news" className={styles.viewAll}>
            {t('listings.details')} →
          </Link>
        </div>

        <div className={styles.grid}>
          {announcements.slice(0, 3).map((item) => (
            <div key={item.id} className={styles.newsCard}>
              <span style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: 700, marginBottom: '0.5rem' }}>
                {t('govNews.source')}: {item.source_name}
              </span>
              <h3 className={styles.newsTitle}>{item.title}</h3>
              <p className={styles.newsSummary}>{item.ai_summary || item.body.substring(0, 120) + '...'}</p>
              <a href={item.source_url} target="_blank" rel="noreferrer" style={{ marginTop: 'auto', fontSize: '0.85rem', color: 'var(--primary)', fontWeight: '700' }}>
                {t('govNews.officialSource')} →
              </a>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Home;
