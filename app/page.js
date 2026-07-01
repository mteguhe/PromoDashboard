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

  // States for adding promo from social media
  const [inputUrl, setInputUrl] = useState('');
  const [inputText, setInputText] = useState('');
  const [showTextFallback, setShowTextFallback] = useState(false);
  const [adding, setAdding] = useState(false);
  const [addSuccess, setAddSuccess] = useState(null);
  const [addError, setAddError] = useState(null);

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

  const handleAddPromo = async (e) => {
    e.preventDefault();
    if (!inputUrl) return;
    setAdding(true);
    setAddError(null);
    setAddSuccess(null);
    try {
      const res = await fetch('/api/scrape/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: inputUrl, text: inputText })
      });
      const result = await res.json();
      if (result.success) {
        setAddSuccess(`Promo "${result.data.title}" berhasil ditambahkan!`);
        setInputUrl('');
        setInputText('');
        setShowTextFallback(false);
        // Automatically switch to the category of the added promo
        const addedCategory = result.data.category || 'flight';
        setCategory(addedCategory);
        fetchPromos();
      } else {
        if (result.error && result.error.includes("Could not extract text") && !showTextFallback) {
          setShowTextFallback(true);
          setAddError("Platform ini membatasi pengambilan otomatis. Silakan tempelkan (paste) teks/caption postingan tersebut di bawah:");
        } else {
          setAddError(result.error || 'Gagal menambahkan promo.');
        }
      }
    } catch (err) {
      console.error(err);
      setAddError('Terjadi kesalahan koneksi saat memproses URL.');
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <h1 className="title-logo">🎟 PromoPortal</h1>
        <div>
          <span className="badge-scraper">Sync: 8:00 & 15:00 WIB</span>
        </div>
      </header>

      {/* Add Custom Promo from Social Media */}
      <div className="add-promo-card">
        <h3 className="add-promo-title">✨ Tambah Promo Instan dari Sosmed</h3>
        <p className="add-promo-subtitle">Tempel link dari Threads, Instagram, atau situs promo lainnya.</p>
        
        <form onSubmit={handleAddPromo} className="add-promo-form">
          <div className="add-promo-row">
            <input 
              type="url" 
              placeholder="https://www.threads.net/@user/post/..." 
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              className="add-promo-input"
              disabled={adding}
              required
            />
            <button 
              type="submit" 
              className="btn-add-promo" 
              disabled={adding || !inputUrl}
            >
              {adding ? 'Memproses...' : 'Tambah Promo'}
            </button>
          </div>

          {showTextFallback && (
            <div className="fallback-container">
              <textarea
                placeholder="Tempel teks lengkap postingan di sini (misal: 'Jakarta Shanghai PP 3juta...')"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="add-promo-textarea"
                rows={4}
                disabled={adding}
                required
              />
            </div>
          )}

          {addSuccess && <div className="alert alert-success">{addSuccess}</div>}
          {addError && <div className="alert alert-error">{addError}</div>}
        </form>
      </div>

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
        <div 
          className={`tab ${category === 'fashion' ? 'active' : ''}`}
          onClick={() => { setCategory('fashion'); setSearch(''); }}
        >
          👗 Fashion
        </div>
        <div 
          className={`tab ${category === 'entertainment' ? 'active' : ''}`}
          onClick={() => { setCategory('entertainment'); setSearch(''); }}
        >
          🎭 Hiburan (Entertainment)
        </div>
        <div
          className={`tab ${category === 'event' ? 'active' : ''}`}
          onClick={() => { setCategory('event'); setSearch(''); }}
        >
          📅 Pameran & Event
        </div>
        <div
          className={`tab ${category === 'hotel' ? 'active' : ''}`}
          onClick={() => { setCategory('hotel'); setSearch(''); }}
        >
          🏨 Hotel
        </div>
      </div>

      {/* Search */}
      <input 
        type="text" 
        className="search-box"
        placeholder={`Cari promo ${
          category === 'flight' ? 'maskapai, kota, rute' :
          category === 'food' ? 'restoran, makanan, brand kuliner' :
          category === 'fashion' ? 'brand pakaian, sepatu, tas' :
          category === 'entertainment' ? 'bioskop, tiket nonton, rekreasi' :
          category === 'hotel' ? 'nama hotel, kota, bintang' :
          'nama pameran, bazaar, expo'
        }...`}
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
