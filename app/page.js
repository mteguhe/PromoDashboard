'use client';
import { useState, useEffect } from 'react';
import PromoCard from '@/components/PromoCard';

export default function Home() {
  const [category, setCategory] = useState('flight'); // flight atau food
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [promos, setPromos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Debouncing search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchPromos = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/promos?category=${category}&search=${encodeURIComponent(debouncedSearch)}`);
      if (!res.ok) {
        throw new Error(`HTTP Error: ${res.status}`);
      }
      const result = await res.json();
      if (result.success) {
        setPromos(result.data);
      } else {
        setError(result.error || 'Gagal memuat promo.');
      }
    } catch (err) {
      console.error(err);
      setError('Terjadi kesalahan koneksi saat memuat promo. Silakan coba kembali.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPromos();
  }, [category, debouncedSearch]);

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <h1 className="title-logo">🎟 PromoPortal</h1>
        <div>
          <span className="badge-scraper">Sync: 8:00 & 15:00 WIB</span>
        </div>
      </header>

      {/* Tab Switcher */}
      <div className="tabs">
        <div 
          className={`tab ${category === 'flight' ? 'active' : ''}`}
          onClick={() => { setCategory('flight'); setSearch(''); }}
        >
          ✈ Penerbangan (Flights)
        </div>
        <div 
          className={`tab ${category === 'food' ? 'active' : ''}`}
          onClick={() => { setCategory('food'); setSearch(''); }}
        >
          🍔 Makanan & Minuman (Food)
        </div>
      </div>

      {/* Search */}
      <input 
        type="text" 
        className="search-box"
        placeholder={`Cari promo ${category === 'flight' ? 'maskapai, kota, rute' : 'brand, kategori kuliner'}...`}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {/* Promo List */}
      {error ? (
        <div className="error-container">
          <p>{error}</p>
          <button className="btn-retry" onClick={fetchPromos}>Coba Lagi</button>
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          Sedang memuat promo terbaik...
        </div>
      ) : promos.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          Tidak ada promo ditemukan.
        </div>
      ) : (
        <div className="promo-grid">
          {promos.map((promo) => (
            <PromoCard key={promo.id} promo={promo} category={category} />
          ))}
        </div>
      )}
    </div>
  );
}
