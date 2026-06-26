'use client';
import { useState, useEffect } from 'react';
import PromoCard from '@/components/PromoCard';
import '@/app/globals.css';

export default function Home() {
  const [category, setCategory] = useState('flight'); // flight atau food
  const [search, setSearch] = useState('');
  const [promos, setPromos] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchPromos = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/promos?category=${category}&search=${encodeURIComponent(search)}`);
      const result = await res.json();
      if (result.success) {
        setPromos(result.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPromos();
  }, [category, search]);

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <div className="title-logo">🎟 PromoPortal</div>
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
      {loading ? (
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
