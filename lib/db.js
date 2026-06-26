import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

let dbPromise = null;

export async function getDbConnection() {
  if (!dbPromise) {
    dbPromise = (async () => {
      try {
        const connection = await open({
          filename: process.env.DATABASE_PATH || path.join(process.cwd(), 'promo.db'),
          driver: sqlite3.Database
        });
        await connection.exec('PRAGMA journal_mode=WAL;');
        await connection.exec('PRAGMA busy_timeout = 30000;');
        return connection;
      } catch (err) {
        dbPromise = null; // Clear cache on failure to allow retry
        throw err;
      }
    })();
  }
  return dbPromise;
}
