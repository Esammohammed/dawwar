import React, { useState } from 'react';
import { X, Mail, LogIn, UserPlus } from 'lucide-react';
import api from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { useTranslation } from '../i18n/i18nContext';
import styles from './AuthModal.module.css';

const AuthModal = ({ onClose }) => {
  const { t } = useTranslation();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  // login views: 'password' | 'otpEmail' | 'otpCode' | 'resetEmail' | 'resetConfirm'
  // register views: 'form' | 'verify'
  const [view, setView] = useState('password');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [fullName, setFullName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const { setAuth } = useAuthStore();

  const getErrorMessage = (err, fallback) => {
    const data = err.response?.data;
    if (data) {
      if (typeof data.code === 'string') {
        const mapped = t(`auth.errors.${data.code}`);
        if (mapped !== `auth.errors.${data.code}`) return mapped;
      }
      if (typeof data.error === 'string') return data.error;
      if (typeof data.detail === 'string') return data.detail;
      for (const field of ['email', 'phone', 'code', 'password', 'new_password', 'full_name', 'identifier']) {
        if (data[field]) return Array.isArray(data[field]) ? data[field][0] : data[field];
      }
    }
    return fallback;
  };

  const switchMode = (nextMode) => {
    setMode(nextMode);
    setView(nextMode === 'login' ? 'password' : 'form');
    setError('');
    setNotice('');
  };

  const goToView = (nextView, noticeText = '') => {
    setView(nextView);
    setError('');
    setNotice(noticeText);
  };

  const finishAuth = (res) => {
    setAuth(res.data.user, res.data.access, res.data.refresh);
    onClose();
  };

  const run = async (fn, fallbackError) => {
    setLoading(true);
    setError('');
    try {
      await fn();
    } catch (err) {
      setError(getErrorMessage(err, fallbackError));
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = (e) => {
    e.preventDefault();
    run(async () => {
      try {
        const res = await api.post('/auth/login/', { identifier, password });
        finishAuth(res);
      } catch (err) {
        if (err.response?.data?.code === 'password_not_set') {
          if (identifier.includes('@')) setEmail(identifier);
          goToView('otpEmail', t('auth.errors.password_not_set'));
          return;
        }
        throw err;
      }
    }, t('auth.errors.invalid_credentials'));
  };

  const handleOtpRequest = (e) => {
    e.preventDefault();
    run(async () => {
      await api.post('/auth/login/otp/request/', { email });
      goToView('otpCode');
    }, t('auth.errors.invalid_code'));
  };

  const handleOtpVerify = (e) => {
    e.preventDefault();
    run(async () => {
      const res = await api.post('/auth/login/otp/verify/', { email, code });
      finishAuth(res);
    }, t('auth.errors.invalid_code'));
  };

  const handleResetRequest = (e) => {
    e.preventDefault();
    run(async () => {
      await api.post('/auth/password/reset/request/', { email });
      goToView('resetConfirm');
    }, t('auth.errors.invalid_code'));
  };

  const handleResetConfirm = (e) => {
    e.preventDefault();
    run(async () => {
      const res = await api.post('/auth/password/reset/confirm/', {
        email,
        code,
        new_password: newPassword,
      });
      finishAuth(res);
    }, t('auth.errors.invalid_code'));
  };

  const handleRegisterRequest = (e) => {
    e.preventDefault();
    run(async () => {
      await api.post('/auth/register/request-otp/', { phone, email });
      goToView('verify');
    }, t('auth.errors.invalid_code'));
  };

  const handleRegisterVerify = (e) => {
    e.preventDefault();
    run(async () => {
      const res = await api.post('/auth/register/verify/', {
        phone,
        email,
        code,
        full_name: fullName,
        password,
      });
      finishAuth(res);
    }, t('auth.errors.invalid_code'));
  };

  const errorBox = error && <div className={styles.errorNotice}>{error}</div>;
  const noticeBox = notice && <div className={styles.otpNotice}>{notice}</div>;

  const emailInput = (
    <div className={styles.inputGroup}>
      <label className={styles.label}>{t('auth.emailLabel')}</label>
      <input
        type="email"
        dir="ltr"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="example@domain.com"
        className={styles.input}
        required
      />
    </div>
  );

  const codeInput = (
    <div className={styles.inputGroup}>
      <label className={styles.label}>{t('auth.codeLabel')}</label>
      <input
        type="text"
        dir="ltr"
        inputMode="numeric"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="••••••"
        className={styles.input}
        maxLength={6}
        required
      />
    </div>
  );

  const renderLogin = () => {
    if (view === 'otpEmail') {
      return (
        <form onSubmit={handleOtpRequest}>
          <h3 className={styles.title}>{t('auth.otpLoginTitle')}</h3>
          <p className={styles.subtitle}>{t('auth.otpLoginSubtitle')}</p>
          {noticeBox}
          {errorBox}
          {emailInput}
          <button type="submit" disabled={loading} className={styles.submitBtn}>
            <Mail size={16} style={{ display: 'inline', marginLeft: '8px', verticalAlign: 'middle' }} />
            {loading ? t('auth.sending') : t('auth.sendOtp')}
          </button>
          <button type="button" className={styles.secondaryBtn} onClick={() => goToView('password')}>
            {t('auth.backToPassword')}
          </button>
        </form>
      );
    }

    if (view === 'otpCode') {
      return (
        <form onSubmit={handleOtpVerify}>
          <h3 className={styles.title}>{t('auth.confirmTitle')}</h3>
          <p className={styles.subtitle}>{t('auth.confirmSubtitleEmail')} {email}</p>
          <div className={styles.otpNotice}>{t('auth.emailNotice')}</div>
          {errorBox}
          {codeInput}
          <button type="submit" disabled={loading} className={styles.submitBtn}>
            {loading ? t('auth.verifying') : t('auth.confirmBtn')}
          </button>
          <button type="button" className={styles.secondaryBtn} onClick={() => goToView('otpEmail')}>
            {t('auth.changeMethod')}
          </button>
        </form>
      );
    }

    if (view === 'resetEmail') {
      return (
        <form onSubmit={handleResetRequest}>
          <h3 className={styles.title}>{t('auth.resetTitle')}</h3>
          <p className={styles.subtitle}>{t('auth.resetSubtitle')}</p>
          {errorBox}
          {emailInput}
          <button type="submit" disabled={loading} className={styles.submitBtn}>
            {loading ? t('auth.sending') : t('auth.sendOtp')}
          </button>
          <button type="button" className={styles.secondaryBtn} onClick={() => goToView('password')}>
            {t('auth.backToPassword')}
          </button>
        </form>
      );
    }

    if (view === 'resetConfirm') {
      return (
        <form onSubmit={handleResetConfirm}>
          <h3 className={styles.title}>{t('auth.resetTitle')}</h3>
          <p className={styles.subtitle}>{t('auth.confirmSubtitleEmail')} {email}</p>
          <div className={styles.otpNotice}>{t('auth.emailNotice')}</div>
          {errorBox}
          {codeInput}
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('auth.newPasswordLabel')}</label>
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
          <button type="submit" disabled={loading} className={styles.submitBtn}>
            {loading ? t('auth.verifying') : t('auth.resetBtn')}
          </button>
          <button type="button" className={styles.secondaryBtn} onClick={() => goToView('resetEmail')}>
            {t('auth.changeMethod')}
          </button>
        </form>
      );
    }

    return (
      <form onSubmit={handlePasswordLogin}>
        <h3 className={styles.title}>{t('auth.loginTitle')}</h3>
        <p className={styles.subtitle}>{t('auth.loginSubtitle')}</p>
        {noticeBox}
        {errorBox}
        <div className={styles.inputGroup}>
          <label className={styles.label}>{t('auth.identifierLabel')}</label>
          <input
            type="text"
            dir="ltr"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="01xxxxxxxxx / example@domain.com"
            className={styles.input}
            required
          />
        </div>
        <div className={styles.inputGroup}>
          <label className={styles.label}>{t('auth.passwordLabel')}</label>
          <input
            type="password"
            dir="ltr"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.input}
            required
          />
        </div>
        <button type="submit" disabled={loading} className={styles.submitBtn}>
          <LogIn size={16} style={{ display: 'inline', marginLeft: '8px', verticalAlign: 'middle' }} />
          {loading ? t('auth.verifying') : t('auth.loginBtn')}
        </button>
        <div className={styles.linkRow}>
          <button type="button" className={styles.linkBtn} onClick={() => goToView('otpEmail')}>
            {t('auth.loginWithCode')}
          </button>
          <button type="button" className={styles.linkBtn} onClick={() => goToView('resetEmail')}>
            {t('auth.forgotPassword')}
          </button>
        </div>
      </form>
    );
  };

  const renderRegister = () => {
    if (view === 'verify') {
      return (
        <form onSubmit={handleRegisterVerify}>
          <h3 className={styles.title}>{t('auth.confirmTitle')}</h3>
          <p className={styles.subtitle}>{t('auth.confirmSubtitleEmail')} {email}</p>
          <div className={styles.otpNotice}>{t('auth.emailNotice')}</div>
          {errorBox}
          {codeInput}
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('auth.fullNameLabel')}</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder={t('auth.fullNamePlaceholder')}
              className={styles.input}
              required
            />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>{t('auth.passwordLabel')}</label>
            <input
              type="password"
              dir="ltr"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={styles.input}
              required
            />
            <span className={styles.hint}>{t('auth.passwordHint')}</span>
          </div>
          <button type="submit" disabled={loading} className={styles.submitBtn}>
            {loading ? t('auth.verifying') : t('auth.createAccountBtn')}
          </button>
          <button type="button" className={styles.secondaryBtn} onClick={() => goToView('form')}>
            {t('auth.changeMethod')}
          </button>
        </form>
      );
    }

    return (
      <form onSubmit={handleRegisterRequest}>
        <h3 className={styles.title}>{t('auth.registerTitle')}</h3>
        <p className={styles.subtitle}>{t('auth.registerSubtitle')}</p>
        {errorBox}
        <div className={styles.inputGroup}>
          <label className={styles.label}>{t('auth.phoneLabel')}</label>
          <input
            type="text"
            dir="ltr"
            inputMode="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="01xxxxxxxxx"
            className={styles.input}
            required
          />
        </div>
        {emailInput}
        <button type="submit" disabled={loading} className={styles.submitBtn}>
          <Mail size={16} style={{ display: 'inline', marginLeft: '8px', verticalAlign: 'middle' }} />
          {loading ? t('auth.sending') : t('auth.sendOtp')}
        </button>
      </form>
    );
  };

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeBtn} onClick={onClose}>
          <X size={18} />
        </button>

        <div className={styles.methodTabs}>
          <button
            type="button"
            className={`${styles.tabBtn} ${mode === 'login' ? styles.tabBtnActive : ''}`}
            onClick={() => switchMode('login')}
          >
            <LogIn size={14} style={{ display: 'inline', marginLeft: '6px', verticalAlign: 'middle' }} />
            {t('auth.loginTab')}
          </button>
          <button
            type="button"
            className={`${styles.tabBtn} ${mode === 'register' ? styles.tabBtnActive : ''}`}
            onClick={() => switchMode('register')}
          >
            <UserPlus size={14} style={{ display: 'inline', marginLeft: '6px', verticalAlign: 'middle' }} />
            {t('auth.registerTab')}
          </button>
        </div>

        {mode === 'login' ? renderLogin() : renderRegister()}
      </div>
    </div>
  );
};

export default AuthModal;
