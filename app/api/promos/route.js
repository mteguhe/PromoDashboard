import { NextResponse } from 'next/server';
import { getDbConnection } from '@/lib/db';

export const dynamic = 'force-dynamic';


export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get('category') || 'flight'; // flight atau food
    if (category !== 'flight' && category !== 'food') {
      return NextResponse.json(
        { success: false, error: 'Invalid category. Must be flight or food.' },
        { status: 400 }
      );
    }
    const search = searchParams.get('search') || '';
    
    const db = await getDbConnection();
    let promos = [];

    if (category === 'flight') {
      let query = 'SELECT * FROM flight_promos WHERE 1=1';
      const params = [];
      if (search) {
        query += ' AND (title LIKE ? OR description LIKE ? OR airline LIKE ?)';
        params.push(`%${search}%`, `%${search}%`, `%${search}%`);
      }
      query += ' ORDER BY created_at DESC';
      promos = await db.all(query, params);
    } else {
      let query = 'SELECT * FROM food_promos WHERE 1=1';
      const params = [];
      if (search) {
        query += ' AND (title LIKE ? OR description LIKE ? OR brand_name LIKE ?)';
        params.push(`%${search}%`, `%${search}%`, `%${search}%`);
      }
      query += ' ORDER BY created_at DESC';
      promos = await db.all(query, params);
    }

    return NextResponse.json({ success: true, data: promos });
  } catch (error) {
    console.error('API Promos Error:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
