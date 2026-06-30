import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export const dynamic = 'force-dynamic';

export async function POST(request) {
  return new Promise((resolve) => {
    const workspaceRoot = process.cwd();
    const pythonPath = path.join(workspaceRoot, '.venv', 'bin', 'python');
    const scriptPath = path.join(workspaceRoot, 'scraper', 'engine.py');
    
    // Command to execute the scraper with real sources
    const command = `PYTHONPATH="${workspaceRoot}" "${pythonPath}" "${scriptPath}" --real`;

    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`Scrape API Error: ${error}`);
        console.error(`Scrape API Stderr: ${stderr}`);
        resolve(NextResponse.json(
          { success: false, error: error.message, details: stderr },
          { status: 500 }
        ));
        return;
      }

      console.log(`Scrape API Success: ${stdout}`);
      resolve(NextResponse.json({
        success: true,
        message: 'Scraping completed successfully.',
        output: stdout
      }));
    });
  });
}
