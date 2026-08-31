import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, ArrowRight, Calculator } from 'lucide-react';
import { useTranslation } from '../../i18n/i18nContext';
import styles from './ExitLanding.module.css';

const ExitLanding = () => {
  const { t } = useTranslation();

  return (
    <div className={styles.page}>
      <div className={styles.hero}>
        <div className={styles.badge}>
          <ShieldCheck size={18} />
          <span>{t('exitDeals.badge')}</span>
        </div>
        
        <h1 className={styles.title}>{t('exitDeals.title')}</h1>
        <p className={styles.subtitle}>{t('exitDeals.introTitle')}</p>

        <div className={styles.checklist}>
          <div className={styles.checkItem}>
            <ShieldCheck className={styles.checkIcon} />
            <span>{t('exitDeals.introChecklist1')}</span>
          </div>
          <div className={styles.checkItem}>
            <ShieldCheck className={styles.checkIcon} />
            <span>{t('exitDeals.introChecklist2')}</span>
          </div>
          <div className={styles.checkItem}>
            <ShieldCheck className={styles.checkIcon} />
            <span>{t('exitDeals.introChecklist3')}</span>
          </div>
          <div className={styles.checkItem}>
            <ShieldCheck className={styles.checkIcon} />
            <span>{t('exitDeals.introChecklist4')}</span>
          </div>
        </div>
        
        <p className={styles.ownersOnly}>{t('exitDeals.ownersOnly')}</p>

        <div className={styles.actions}>
          <Link to="/exit/sell" className={styles.primaryBtn}>
            {t('exitDeals.ctaSell')}
            <ArrowRight size={18} />
          </Link>
          <Link to="/exit/calculator" className={styles.secondaryBtn}>
            <Calculator size={18} />
            {t('exitDeals.ctaCalculator')}
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ExitLanding;
