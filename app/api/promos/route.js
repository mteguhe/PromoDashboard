import { NextResponse } from 'next/server';
import { getDbConnection } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get('category') || 'flight';
    const validCategories = ['flight', 'food', 'fashion', 'event', 'entertainment'];
    if (!validCategories.includes(category)) {
      return NextResponse.json(
        { success: false, error: `Invalid category. Must be one of: ${validCategories.join(', ')}` },
        { status: 400 }
      );
    }
    const search = searchParams.get('search') || '';
    const db = await getDbConnection();

    let query = 'SELECT * FROM promos WHERE category = ?';
    const params = [category];
    if (search) {
      query += ' AND (title LIKE ? OR description LIKE ? OR brand_name LIKE ?)';
      params.push(`%${search}%`, `%${search}%`, `%${search}%`);
    }
    query += ' ORDER BY created_at DESC';

    const promos = await db.all(query, params);
    return NextResponse.json({ success: true, data: promos });
  } catch (error) {
    console.error('API Promos Error:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
