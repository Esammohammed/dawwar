import React, { useState } from 'react';
import { X, ShieldCheck, Clock } from 'lucide-react';
import api from '../api/client';
import { useTranslation } from '../i18n/i18nContext';
import styles from './AuthModal.module.css';

const BookingModal = ({ listing, onClose }) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(null);
  const [error, setError] = useState('');

  const handleCreateBooking = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/bookings/', {
        listing: listing.id,
        deposit_amount: 10000,
      });
      setBooking(res.data);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError('Failed to process booking. Ensure you are logged in.');
      }
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

        {booking ? (
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <ShieldCheck size={48} style={{ color: '#16a34a', margin: '0 auto 1rem' }} />
            <h3 className={styles.title} style={{ color: '#16a34a' }}>{t('bookingModal.successTitle')}</h3>
            <p className={styles.subtitle}>
              {t('bookingModal.bookingNo')} <strong>{booking.id.substring(0, 8)}</strong>
            </p>
            <div className={styles.otpNotice}>
              <Clock size={16} style={{ display: 'inline', margin: '0 4px' }} />
              {t('bookingModal.expiryNotice')}
            </div>
            <button onClick={onClose} className={styles.submitBtn}>{t('bookingModal.close')}</button>
          </div>
        ) : (
          <div>
            <h3 className={styles.title}>{t('bookingModal.title')}</h3>
            <p className={styles.subtitle}>{t('bookingModal.subtitle')} {listing.title}</p>

            {error && <div className={styles.otpNotice} style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#991b1b' }}>{error}</div>}

            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '12px', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                <span>{t('bookingModal.depositLabel')}</span>
                <strong>{t('bookingModal.depositValue')}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#64748b' }}>
                <span>{t('bookingModal.lockNotice')}</span>
              </div>
            </div>

            <button onClick={handleCreateBooking} disabled={loading} className={styles.submitBtn}>
              {loading ? '...' : t('bookingModal.confirmBtn')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default BookingModal;
