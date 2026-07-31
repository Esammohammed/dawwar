import React, { useEffect, useState } from 'react';
import { Newspaper, ExternalLink, Sparkles } from 'lucide-react';
import api from '../api/client';
import { useTranslation } from '../i18n/i18nContext';
import styles from './GovNews.module.css';

const GovNews = () => {
  const { t } = useTranslation();
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await api.get('/announcements/');
        setAnnouncements(res.data.results || res.data || []);
      } catch (err) {
        console.error('Error fetching news:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
  }, []);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          <Newspaper className={styles.titleIcon} />
          {t('govNews.title')}
        </h1>
        <p className={styles.subtitle}>{t('govNews.subtitle')}</p>
      </div>

      {loading ? (
        <div className={styles.loadingState}>{t('govNews.loading')}</div>
      ) : (
        <div className={styles.list}>
          {announcements.map((item) => (
            <div key={item.id} className={styles.newsCard}>
              <div className={styles.cardHeader}>
                <span className={styles.sourceBadge}>
                  {t('govNews.source')}: {item.source_name}
                </span>
                <span className={styles.date}>
                  {new Date(item.scraped_at).toLocaleDateString()}
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

              <a
                href={item.source_url}
                target="_blank"
                rel="noreferrer"
                className={styles.sourceLink}
              >
                {t('govNews.officialSource')} <ExternalLink size={16} />
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GovNews;
