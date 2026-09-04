import React, { useEffect, useState } from 'react';
import { Newspaper, ExternalLink, Sparkles, ClipboardList, MessageCircle } from 'lucide-react';
import api from '../api/client';
import { useTranslation } from '../i18n/i18nContext';
import { DAWWAR_SUPPORT_PHONE_INTL } from '../constants/contact';
import styles from './GovNews.module.css';

const GovNews = () => {
  const { t } = useTranslation();
  const [announcements, setAnnouncements] = useState([]);
  const [projects, setProjects] = useState([]);
  const [programFilter, setProgramFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      setLoading(true);
      try {
        const params = programFilter ? { project: programFilter } : {};
        const res = await api.get('/announcements/', { params });
        setAnnouncements(res.data.results || res.data || []);
      } catch (err) {
        console.error('Error fetching news:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
  }, [programFilter]);

  useEffect(() => {
    // Populates the program filter dropdown — safe to fail silently, the
    // page still works fine with just the unfiltered feed.
    api.get('/projects/', { params: { type: 'government' } })
      .then((res) => setProjects(res.data.results || res.data || []))
      .catch(() => {});
  }, []);

  const whatsappUrl = `https://wa.me/${DAWWAR_SUPPORT_PHONE_INTL}?text=${encodeURIComponent(t('govNews.helpCta'))}`;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          <Newspaper className={styles.titleIcon} />
          {t('govNews.title')}
        </h1>
        <p className={styles.subtitle}>{t('govNews.subtitle')}</p>
      </div>

      {projects.length > 0 && (
        <div className={styles.filterRow}>
          <select
            value={programFilter}
            onChange={(e) => setProgramFilter(e.target.value)}
            className={styles.programSelect}
          >
            <option value="">{t('govNews.allPrograms')}</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      )}

      {loading ? (
        <div className={styles.loadingState}>{t('govNews.loading')}</div>
      ) : (
        <div className={styles.list}>
          {announcements.map((item) => (
            <div key={item.id} className={styles.newsCard}>
              <div className={styles.cardHeader}>
                <div className={styles.badgeGroup}>
                  <span className={styles.sourceBadge}>
                    {t('govNews.source')}: {item.source_name}
                  </span>
                  {item.project_details && (
                    <span className={styles.programBadge}>{item.project_details.name}</span>
                  )}
                </div>
                <span className={styles.date}>
                  {new Date(item.published_at || item.scraped_at).toLocaleDateString()}
                </span>
              </div>

              <h2 className={styles.cardTitle}>{item.title}</h2>

              {item.ai_summary && (
                <div className={styles.aiBox}>
                  <div className={styles.aiLabel}>
                    <Sparkles size={16} /> {t('govNews.aiSummary')}
                  </div>
                  {item.ai_summary}
                </div>
              )}

              <p className={styles.cardBody}>{item.body}</p>

              {/* item.requirements is only ever populated when the source
                  article itself explicitly stated conditions/papers — null
                  means "not mentioned", never "confirmed none required", so
                  the copy here must not overstate this as a complete list. */}
              {item.requirements && item.requirements.length > 0 && (
                <div className={styles.requirementsBox}>
                  <div className={styles.requirementsLabel}>
                    <ClipboardList size={16} /> {t('govNews.requirementsTitle')}
                  </div>
                  <ul className={styles.requirementsList}>
                    {item.requirements.map((req, i) => <li key={i}>{req}</li>)}
                  </ul>
                  <p className={styles.requirementsNote}>{t('govNews.requirementsNote')}</p>
                </div>
              )}

              <div className={styles.cardFooter}>
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className={styles.sourceLink}
                >
                  {t('govNews.officialSource')} <ExternalLink size={16} />
                </a>

                <a href={whatsappUrl} target="_blank" rel="noreferrer" className={styles.helpCtaBtn}>
                  <MessageCircle size={16} />
                  {t('govNews.helpCtaBtn')}
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GovNews;
