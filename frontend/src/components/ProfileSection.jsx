import React, { useEffect, useState } from 'react';
import { Save, KeyRound } from 'lucide-react';
import api from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { useTranslation } from '../i18n/i18nContext';
import { GovernorateSelect, CitySelect } from './LocationSelects';
import styles from './ProfileSection.module.css';

const ProfileSection = () => {
  const { t } = useTranslation();
  const { setUser } = useAuthStore();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({
    full_name: '',
    address: '',
    governorate: '',
    city: '',
    date_of_birth: '',
    national_id: '',
  });
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [saveError, setSaveError] = useState('');

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');

  useEffect(() => {
    api.get('/me/').then((res) => {
      setProfile(res.data);
      setUser(res.data);
      setForm({
        full_name: res.data.full_name || '',
        address: res.data.address || '',
        governorate: res.data.governorate || '',
        city: res.data.city || '',
        date_of_birth: res.data.date_of_birth || '',
        national_id: res.data.national_id || '',
      });
    }).catch((err) => {
      console.error('Error fetching profile:', err);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getErrorMessage = (err, fallback) => {
    const data = err.response?.data;
    if (data) {
      if (typeof data.code === 'string') {
        const mapped = t(`auth.errors.${data.code}`);
        if (mapped !== `auth.errors.${data.code}`) return mapped;
      }
      if (typeof data.error === 'string') return data.error;
      for (const field of ['full_name', 'address', 'governorate', 'city', 'date_of_birth', 'national_id', 'current_password', 'new_password']) {
        if (data[field]) return Array.isArray(data[field]) ? data[field][0] : data[field];
      }
    }
    return fallback;
  };

  const setField = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleGovernorateChange = (e) => {
    const { value } = e.target;
    setForm((prev) => ({ ...prev, governorate: value, city: '' }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveMessage('');
    setSaveError('');
    try {
      const payload = { ...form };
      if (!payload.date_of_birth) payload.date_of_birth = null;
      const res = await api.patch('/me/', payload);
      setProfile(res.data);
      setUser(res.data);
      setSaveMessage(t('account.saved'));
    } catch (err) {
      setSaveError(getErrorMessage(err, t('account.saveFailed')));
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordSaving(true);
    setPasswordMessage('');
    setPasswordError('');
    try {
      const payload = { new_password: newPassword };
      if (profile?.has_password) payload.current_password = currentPassword;
      const res = await api.post('/auth/password/change/', payload);
      setProfile(res.data);
      setUser(res.data);
      setCurrentPassword('');
      setNewPassword('');
      setPasswordMessage(t('account.passwordChanged'));
    } catch (err) {
      setPasswordError(getErrorMessage(err, t('account.saveFailed')));
    } finally {
      setPasswordSaving(false);
    }
  };

  if (!profile) {
    return <div className={styles.loadingState}>...</div>;
  }

  return (
    <div className={styles.wrapper}>
      <form className={styles.card} onSubmit={handleSave}>
        <h3 className={styles.cardTitle}>{t('account.profileTab')}</h3>

        {saveMessage && <div className={styles.successNotice}>{saveMessage}</div>}
        {saveError && <div className={styles.errorNotice}>{saveError}</div>}

        <div className={styles.grid}>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('auth.fullNameLabel')}</label>
            <input
              type="text"
              value={form.full_name}
              onChange={setField('full_name')}
              className={styles.input}
              required
            />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('auth.phoneLabel')}</label>
            <input type="text" dir="ltr" value={profile.phone} className={styles.input} disabled />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('auth.emailLabel')}</label>
            <input type="text" dir="ltr" value={profile.email || ''} className={styles.input} disabled />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('account.addressLabel')}</label>
            <input
              type="text"
              value={form.address}
              onChange={setField('address')}
              className={styles.input}
            />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('account.governorateLabel')}</label>
            <GovernorateSelect
              mode="profile"
              value={form.governorate}
              onChange={handleGovernorateChange}
              className={styles.input}
            />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('account.cityLabel')}</label>
            <CitySelect
              mode="profile"
              governorate={form.governorate}
              value={form.city}
              onChange={setField('city')}
              className={styles.input}
            />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('account.dobLabel')}</label>
            <input
              type="date"
              dir="ltr"
              value={form.date_of_birth || ''}
              onChange={setField('date_of_birth')}
              className={styles.input}
            />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('account.nationalIdLabel')}</label>
            <input
              type="text"
              dir="ltr"
              inputMode="numeric"
              maxLength={14}
              value={form.national_id}
              onChange={setField('national_id')}
              className={styles.input}
            />
          </div>
        </div>

        <button type="submit" disabled={saving} className={styles.submitBtn}>
          <Save size={16} style={{ display: 'inline', marginLeft: '8px', verticalAlign: 'middle' }} />
          {saving ? t('account.saving') : t('account.save')}
        </button>
      </form>

      <form className={styles.card} onSubmit={handlePasswordSubmit}>
        <h3 className={styles.cardTitle}>
          <KeyRound size={18} style={{ display: 'inline', marginLeft: '8px', verticalAlign: 'middle' }} />
          {t('account.passwordSection')}
        </h3>

        {!profile.has_password && (
          <div className={styles.goldBanner}>{t('account.setPasswordBanner')}</div>
        )}
        {passwordMessage && <div className={styles.successNotice}>{passwordMessage}</div>}
        {passwordError && <div className={styles.errorNotice}>{passwordError}</div>}

        <div className={styles.grid}>
          {profile.has_password && (
            <div className={styles.inputGroup}>
              <label className={styles.label}>{t('account.currentPasswordLabel')}</label>
              <input
                type="password"
                dir="ltr"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className={styles.input}
                required
              />
            </div>
          )}
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('account.newPasswordLabel')}</label>
            <input
              type="password"
              dir="ltr"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={styles.input}
              required
            />
            <span className={styles.hint}>{t('auth.passwordHint')}</span>
          </div>
        </div>

        <button type="submit" disabled={passwordSaving} className={styles.submitBtn}>
          {passwordSaving
            ? t('account.saving')
            : profile.has_password
              ? t('account.changePasswordBtn')
              : t('account.setPasswordBtn')}
        </button>
      </form>
    </div>
  );
};

export default ProfileSection;
