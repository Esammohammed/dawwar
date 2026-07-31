import React, { useEffect, useState } from 'react';
import { User } from 'lucide-react';
import api from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { useTranslation } from '../i18n/i18nContext';
import styles from './Account.module.css';

const Account = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('listings');
  const [myListings, setMyListings] = useState([]);
  const [myBookings, setMyBookings] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const fetchUserData = async () => {
      try {
        const [listingsRes, bookingsRes, appsRes] = await Promise.all([
          api.get('/listings/my-listings/'),
          api.get('/bookings/'),
          api.get('/applications/')
        ]);
        setMyListings(listingsRes.data || []);
        setMyBookings(bookingsRes.data.results || bookingsRes.data || []);
        setMyApplications(appsRes.data.results || appsRes.data || []);
      } catch (err) {
        console.error('Error fetching account data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, [user]);

  if (!user) {
    return (
      <div className={styles.loginPrompt}>
        <h2>Please login to view your account dashboard.</h2>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      
      {/* Profile Header */}
      <div className={styles.profileCard}>
        <div className={styles.avatar}>
          <User size={36} />
        </div>
        <div>
          <h1 className={styles.profileName}>{user.full_name || 'User'}</h1>
          <p className={styles.profileMeta}>Phone: {user.phone} • Verified Account ✓</p>
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        <button
          onClick={() => setActiveTab('listings')}
          className={`${styles.tab} ${activeTab === 'listings' ? styles.tabActive : ''}`}
        >
          {t('account.myListings')} ({myListings.length})
        </button>
        <button
          onClick={() => setActiveTab('bookings')}
          className={`${styles.tab} ${activeTab === 'bookings' ? styles.tabActive : ''}`}
        >
          {t('account.myBookings')} ({myBookings.length})
        </button>
        <button
          onClick={() => setActiveTab('applications')}
          className={`${styles.tab} ${activeTab === 'applications' ? styles.tabActive : ''}`}
        >
          {t('account.myApplications')} ({myApplications.length})
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className={styles.loadingState}>Updating...</div>
      ) : activeTab === 'listings' ? (
        myListings.length > 0 ? (
          <div className={styles.cardGrid}>
            {myListings.map((item) => (
              <div key={item.id} className={styles.itemCard}>
                <div className={styles.itemStatus}>{t('account.status')}: {item.status}</div>
                <h3 className={styles.itemTitle}>{item.title}</h3>
                <div className={styles.itemPrice}>{Number(item.asking_price).toLocaleString()} EGP</div>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.emptyState}>{t('account.noListings')}</div>
        )
      ) : activeTab === 'bookings' ? (
        myBookings.length > 0 ? (
          <div className={styles.bookingList}>
            {myBookings.map((item) => (
              <div key={item.id} className={styles.bookingCard}>
                <div>
                  <div className={styles.itemStatus}>{t('account.status')}: {item.status}</div>
                  <h4 className={styles.itemTitle}>{item.listing_details?.title || `Booking #${item.id.substring(0,8)}`}</h4>
                  <div className={styles.itemMeta}>Deposit: {item.deposit_amount} EGP</div>
                </div>
                <div className={styles.itemMeta}>
                  Expires: {new Date(item.expires_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.emptyState}>{t('account.noBookings')}</div>
        )
      ) : (
        myApplications.length > 0 ? (
          <div className={styles.bookingList}>
            {myApplications.map((item) => (
              <div key={item.id} className={styles.itemCard}>
                <h4>{item.project_details?.name || item.project}</h4>
                <div>{t('account.status')}: {item.status}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.emptyState}>{t('account.noApps')}</div>
        )
      )}

    </div>
  );
};

export default Account;
