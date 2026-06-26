import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

let dbPromise = null;

export async function getDbConnection() {
  if (!dbPromise) {
    dbPromise = (async () => {
      const connection = await open({
        filename: process.env.DATABASE_PATH || path.join(process.cwd(), 'promo.db'),
        driver: sqlite3.Database
      });
      await connection.exec('PRAGMA journal_mode=WAL;');
      return connection;
    })();
  }
  return dbPromise;
}
