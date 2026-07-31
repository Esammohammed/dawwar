import React, { useEffect, useState } from 'react';
import api from '../api/client';
import ListingCard from '../components/ListingCard';
import FilterBar from '../components/FilterBar';
import { useFilterStore } from '../stores/filterStore';
import { useTranslation } from '../i18n/i18nContext';
import styles from './Listings.module.css';

const Listings = () => {
  const { t } = useTranslation();
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const filters = useFilterStore();

  const fetchListings = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.type) params.type = filters.type;
      if (filters.governorate) params.governorate = filters.governorate;
      if (filters.city) params.city = filters.city;
      if (filters.maxPrice) params.max_price = filters.maxPrice;
      if (filters.bedrooms) params.bedrooms = filters.bedrooms;
      if (filters.hasInstallments) params.has_installments = true;

      const res = await api.get('/listings/', { params });
      setListings(res.data.results || res.data || []);
    } catch (err) {
      console.error('Error fetching listings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [filters.type, filters.governorate, filters.city, filters.maxPrice, filters.bedrooms, filters.hasInstallments]);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('listings.title')}</h1>
        <p className={styles.subtitle}>{t('listings.subtitle')}</p>
      </div>

      <FilterBar onSearch={fetchListings} />

      {loading ? (
        <div className={styles.loadingState}>{t('listings.loading')}</div>
      ) : listings.length > 0 ? (
        <div className={styles.grid}>
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          {t('listings.noResults')}
        </div>
      )}
    </div>
  );
};

export default Listings;
