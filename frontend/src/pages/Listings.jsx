import React, { useEffect, useRef, useState, useCallback } from 'react';
import api from '../api/client';
import ListingCard from '../components/ListingCard';
import FilterBar from '../components/FilterBar';
import { useFilterStore } from '../stores/filterStore';
import { useTranslation } from '../i18n/i18nContext';
import styles from './Listings.module.css';

// ─── helpers ──────────────────────────────────────────────────────────────────

const buildParams = (filters) => {
  const p = {};
  if (filters.type)           p.type = filters.type;
  if (filters.propertyType)   p.property_type = filters.propertyType;
  if (filters.governorate)    p.governorate = filters.governorate;
  if (filters.city)           p.city = filters.city;
  if (filters.maxPrice)       p.max_price = filters.maxPrice;
  if (filters.bedrooms)       p.bedrooms = filters.bedrooms;
  if (filters.hasInstallments) p.has_installments = true;
  if (filters.is_verified_exit) p.is_verified_exit = true;
  return p;
};

// ─── Listings ─────────────────────────────────────────────────────────────────

const Listings = () => {
  const { t } = useTranslation();
  const filters = useFilterStore();

  const [listings, setListings]       = useState([]);
  const [nextUrl, setNextUrl]         = useState(null);
  const [total, setTotal]             = useState(0);
  const [loadingFirst, setLoadingFirst] = useState(true);
  const [loadingMore, setLoadingMore]   = useState(false);

  // Sentinel ref — the invisible <div> at the bottom of the list.
  const sentinelRef = useRef(null);
  // Keep a ref to the current nextUrl so the observer callback doesn't close
  // over a stale value.
  const nextUrlRef = useRef(null);
  const loadingMoreRef = useRef(false);

  // ── initial / filter-change fetch ─────────────────────────────────────────

  const fetchFirstPage = useCallback(async () => {
    setLoadingFirst(true);
    setListings([]);
    setNextUrl(null);
    nextUrlRef.current = null;

    try {
      const res = await api.get('/listings/', { params: buildParams(filters) });
      const data = res.data;
      setListings(data.results || data || []);
      setNextUrl(data.next || null);
      nextUrlRef.current = data.next || null;
      setTotal(data.count ?? (data.results?.length ?? (data.length ?? 0)));
    } catch (err) {
      console.error('Error fetching listings:', err);
    } finally {
      setLoadingFirst(false);
    }
  }, [
    filters.type, filters.propertyType, filters.governorate, filters.city,
    filters.maxPrice, filters.bedrooms, filters.hasInstallments, filters.is_verified_exit,
  ]);

  // ── load next page (called by IntersectionObserver) ───────────────────────

  const fetchNextPage = useCallback(async () => {
    if (!nextUrlRef.current || loadingMoreRef.current) return;

    loadingMoreRef.current = true;
    setLoadingMore(true);

    try {
      const res = await api.get(nextUrlRef.current);
      const data = res.data;
      setListings(prev => [...prev, ...(data.results || [])]);
      setNextUrl(data.next || null);
      nextUrlRef.current = data.next || null;
    } catch (err) {
      console.error('Error loading more listings:', err);
    } finally {
      loadingMoreRef.current = false;
      setLoadingMore(false);
    }
  }, []);

  // ── IntersectionObserver: watch the sentinel div ──────────────────────────

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          fetchNextPage();
        }
      },
      { rootMargin: '200px' }   // trigger 200px before the sentinel hits the viewport
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [fetchNextPage]);

  // ── re-fetch on filter change ─────────────────────────────────────────────

  useEffect(() => {
    fetchFirstPage();
  }, [fetchFirstPage]);

  // ─── render ─────────────────────────────────────────────────────────────────

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('listings.title')}</h1>
        <p className={styles.subtitle}>{t('listings.subtitle')}</p>
        {!loadingFirst && total > 0 && (
          <span className={styles.count}>{total} {t('listings.subtitle').split(' ')[0]}</span>
        )}
      </div>

      <FilterBar onSearch={fetchFirstPage} />

      {loadingFirst ? (
        <div className={styles.loadingState}>
          <div className={styles.skeletonGrid}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className={styles.skeletonCard} />
            ))}
          </div>
        </div>
      ) : listings.length > 0 ? (
        <>
          <div className={styles.grid}>
            {listings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>

          {/* Sentinel: IntersectionObserver watches this */}
          <div ref={sentinelRef} className={styles.sentinel} />

          {loadingMore && (
            <div className={styles.loadMoreSpinner}>
              <span className={styles.spinner} />
            </div>
          )}

          {!loadingMore && !nextUrl && listings.length > 0 && (
            <p className={styles.endMessage}>— {t('listings.noResults').split('.')[0]} —</p>
          )}
        </>
      ) : (
        <div className={styles.emptyState}>
          {t('listings.noResults')}
        </div>
      )}
    </div>
  );
};

export default Listings;
