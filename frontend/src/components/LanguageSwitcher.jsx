import React from 'react';
import { Globe } from 'lucide-react';
import { useTranslation } from '../i18n/i18nContext';
import styles from './LanguageSwitcher.module.css';

const LanguageSwitcher = () => {
  const { language, setLanguage } = useTranslation();

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'ar' : 'en');
  };

  return (
    <button onClick={toggleLanguage} className={styles.btn} title="Switch Language">
      <Globe size={16} />
      <span>{language === 'en' ? 'العربية' : 'English'}</span>
    </button>
  );
};

export default LanguageSwitcher;
