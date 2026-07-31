import React from 'react';
import { Link } from 'react-router-dom';
import { Phone, Mail, MapPin } from 'lucide-react';
import { useTranslation } from '../i18n/i18nContext';
import styles from './Footer.module.css';

const Footer = () => {
  const { t } = useTranslation();

  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.grid}>
          
          <div className={styles.brand}>
            <div className={styles.logo}>
              <img src="/dawwar-mark.svg" alt="Dawwar" className={styles.logoMark} />
              <span className={styles.brandTitle}>{t('nav.brand')}</span>
            </div>
            <p className={styles.desc}>
              {t('footer.desc')}
            </p>
          </div>

          <div>
            <h4 className={styles.colTitle}>{t('footer.quickLinks')}</h4>
            <ul className={styles.linkList}>
              <li className={styles.linkItem}><Link to="/listings">{t('footer.resaleLink')}</Link></li>
              <li className={styles.linkItem}><Link to="/projects">{t('footer.projectsLink')}</Link></li>
              <li className={styles.linkItem}><Link to="/gov-news">{t('footer.govNewsLink')}</Link></li>
              <li className={styles.linkItem}><Link to="/sell">{t('footer.sellLink')}</Link></li>
            </ul>
          </div>

          <div>
            <h4 className={styles.colTitle}>{t('footer.topRegions')}</h4>
            <ul className={styles.linkList}>
              <li className={styles.linkItem}><Link to="/listings?city=6th%20of%20October">6th of October & Sheikh Zayed</Link></li>
              <li className={styles.linkItem}><Link to="/listings?city=New%20Cairo">New Cairo & Fifth Settlement</Link></li>
              <li className={styles.linkItem}><Link to="/listings?city=Administrative%20Capital">New Administrative Capital</Link></li>
              <li className={styles.linkItem}><Link to="/listings?city=Shorouk">Shorouk & Badr</Link></li>
            </ul>
          </div>

          <div>
            <h4 className={styles.colTitle}>{t('footer.contactUs')}</h4>
            <div className={styles.contactItem}>
              <Phone size={16} className={styles.contactIcon} />
              <span>+20 100 000 0000</span>
            </div>
            <div className={styles.contactItem}>
              <Mail size={16} className={styles.contactIcon} />
              <span>support@dawwar.eg</span>
            </div>
            <div className={styles.contactItem}>
              <MapPin size={16} className={styles.contactIcon} />
              <span>Cairo, Arab Republic of Egypt</span>
            </div>
          </div>

        </div>

        <div className={styles.bottom}>
          © {new Date().getFullYear()} {t('footer.copyright')}
        </div>
      </div>
    </footer>
  );
};

export default Footer;
