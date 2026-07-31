import React, { useState } from 'react';
import { X } from 'lucide-react';
import api from '../api/client';
import { useTranslation } from '../i18n/i18nContext';
import styles from './AuthModal.module.css';

const InquiryModal = ({ listing, onClose }) => {
  const { t } = useTranslation();
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState(t('inquiryModal.defaultMsg'));
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post('/inquiries/', {
        listing: listing.id,
        phone: phone,
        message: message,
      });
      setSuccess(true);
    } catch (err) {
      setError('An error occurred while sending your request.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeBtn} onClick={onClose}>
          <X size={18} />
        </button>

        {success ? (
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <h3 className={styles.title} style={{ color: '#16a34a' }}>{t('inquiryModal.successTitle')}</h3>
            <p className={styles.subtitle}>{t('inquiryModal.successDesc')}</p>
            <button onClick={onClose} className={styles.submitBtn}>{t('inquiryModal.close')}</button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <h3 className={styles.title}>{t('inquiryModal.title')}</h3>
            <p className={styles.subtitle}>{t('inquiryModal.subtitle')} {listing.title}</p>

            {error && <div className={styles.otpNotice} style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#991b1b' }}>{error}</div>}

            <div className={styles.inputGroup}>
              <label className={styles.label}>{t('inquiryModal.phoneLabel')}</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="01xxxxxxxxx"
                className={styles.input}
                required
              />
            </div>

            <div className={styles.inputGroup}>
              <label className={styles.label}>{t('inquiryModal.messageLabel')}</label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                className={styles.input}
                required
              />
            </div>

            <button type="submit" disabled={loading} className={styles.submitBtn}>
              {loading ? '...' : t('inquiryModal.submitBtn')}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default InquiryModal;
