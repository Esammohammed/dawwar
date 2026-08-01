import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapPin } from 'lucide-react';
import api from '../api/client';
import { useTranslation } from '../i18n/i18nContext';
import styles from './Projects.module.css';

const Projects = () => {
  const { t } = useTranslation();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await api.get('/projects/');
        setProjects(res.data.results || res.data || []);
      } catch (err) {
        console.error('Error fetching projects:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('projects.title')}</h1>
        <p className={styles.subtitle}>{t('projects.subtitle')}</p>
      </div>

      {loading ? (
        <div className={styles.loadingState}>{t('projects.loading')}</div>
      ) : (
        <div className={styles.grid}>
          {projects.map((project) => (
            <Link key={project.id} to={`/projects/${project.slug}`} className={styles.projectCard}>
              <div className={styles.cardImage}>
                <img
                  src={project.cover_image || 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=600&q=80'}
                  alt={project.name}
                />
                <span className={styles.typeBadge}>
                  {project.type === 'government' ? t('projects.govProject') : t('projects.devProject')}
                </span>
              </div>
              <div className={styles.cardBody}>
                <div className={styles.cardLocation}>
                  <MapPin size={14} />
                  <span>{project.governorate} • {project.city}</span>
                </div>
                <h3 className={styles.cardName}>{project.name}</h3>
                <p className={styles.cardDesc}>
                  {project.description || 'Integrated residential project.'}
                </p>
                <div className={styles.cardFooter}>
                  <span className={styles.statusTag}>
                    {t('projects.status')}: {project.status}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default Projects;
