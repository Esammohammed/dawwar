import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { MapPin, Building2 } from 'lucide-react';
import api from '../api/client';
import ListingCard from '../components/ListingCard';
import { useTranslation } from '../i18n/i18nContext';
import styles from './ProjectDetail.module.css';

const ProjectDetail = () => {
  const { slug } = useParams();
  const { t } = useTranslation();
  const [project, setProject] = useState(null);
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const fetchProjectAndListings = async () => {
      setLoading(true);
      try {
        const projectRes = await api.get(`/projects/${slug}/`);
        if (cancelled) return;
        setProject(projectRes.data);

        const listingsRes = await api.get('/listings/', { params: { project: projectRes.data.id } });
        if (cancelled) return;
        setListings(listingsRes.data.results || listingsRes.data || []);
      } catch (err) {
        console.error('Error fetching project details:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchProjectAndListings();
    return () => { cancelled = true; };
  }, [slug]);

  if (loading) {
    return <div className={styles.loadingState}>{t('projects.loading')}</div>;
  }

  if (!project) {
    return <div className={styles.emptyState}>{t('projects.notFound')}</div>;
  }

  return (
    <div className={styles.page}>
      <div className={styles.cover}>
        <img
          src={project.cover_image || 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80'}
          alt={project.name}
        />
      </div>

      <div className={styles.header}>
        <div className={styles.badges}>
          <span className={styles.badge}>
            {project.type === 'government' ? t('projects.govProject') : t('projects.devProject')}
          </span>
          <span className={styles.badge}>{t('projects.status')}: {project.status}</span>
        </div>
        <h1 className={styles.title}>{project.name}</h1>
        <div className={styles.locationRow}>
          <MapPin size={16} />
          <span>{project.governorate} • {project.city}{project.district ? ` (${project.district})` : ''}</span>
        </div>
        {project.developer_details && (
          <div className={styles.developerRow}>
            <Building2 size={16} />
            <span>{project.developer_details.name}</span>
          </div>
        )}
      </div>

      {project.description && (
        <p className={styles.description}>{project.description}</p>
      )}

      <div className={styles.listingsSection}>
        <h2 className={styles.listingsTitle}>
          {t('projects.unitsInProject')} ({listings.length})
        </h2>

        {listings.length > 0 ? (
          <div className={styles.grid}>
            {listings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        ) : (
          <div className={styles.emptyState}>{t('projects.noUnits')}</div>
        )}
      </div>

      <Link to="/projects" className={styles.backLink}>
        {t('projects.backToProjects')}
      </Link>
    </div>
  );
};

export default ProjectDetail;
