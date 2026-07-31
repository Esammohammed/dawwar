import React, { useState } from 'react';
import { X } from 'lucide-react';
import api from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { useTranslation } from '../i18n/i18nContext';
import styles from './AuthModal.module.css';

const AuthModal = ({ onClose }) => {
  const { t } = useTranslation();
  const [step, setStep] = useState(1);
  const [phone, setPhone] = useState('01000000000');
  const [code, setCode] = useState('123456');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { setAuth } = useAuthStore();

  const handleRequestOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post('/auth/otp/request/', { phone });
      setStep(2);
    } catch (err) {
      setError('Failed to send OTP code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/auth/otp/verify/', { phone, code, full_name: fullName });
      setAuth(res.data.user, res.data.access, res.data.refresh);
      onClose();
    } catch (err) {
      setError('Invalid or expired verification code');
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

        {step === 1 ? (
          <form onSubmit={handleRequestOTP}>
            <h3 className={styles.title}>{t('auth.title')}</h3>
            <p className={styles.subtitle}>{t('auth.subtitle')}</p>

            {error && <div className={styles.otpNotice} style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#991b1b' }}>{error}</div>}

            <div className={styles.inputGroup}>
              <label className={styles.label}>{t('auth.phoneLabel')}</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="01xxxxxxxxx"
                className={styles.input}
                required
              />
            </div>

            <button type="submit" disabled={loading} className={styles.submitBtn}>
              {loading ? t('auth.sending') : t('auth.sendOtp')}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP}>
            <h3 className={styles.title}>{t('auth.confirmTitle')}</h3>
            <p className={styles.subtitle}>{t('auth.confirmSubtitle')} {phone}</p>

            <div className={styles.otpNotice}>
              {t('auth.mockNotice')}
            </div>

            {error && <div className={styles.otpNotice} style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#991b1b' }}>{error}</div>}

            <div className={styles.inputGroup}>
              <label className={styles.label}>{t('auth.fullNameLabel')}</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ahmed Mahmoud"
                className={styles.input}
              />
            </div>

            <div className={styles.inputGroup}>
              <label className={styles.label}>{t('auth.codeLabel')}</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="123456"
                className={styles.input}
                maxLength={6}
                required
              />
            </div>

            <button type="submit" disabled={loading} className={styles.submitBtn}>
              {loading ? t('auth.verifying') : t('auth.confirmBtn')}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default AuthModal;
