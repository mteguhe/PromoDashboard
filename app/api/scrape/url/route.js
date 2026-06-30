import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export const dynamic = 'force-dynamic';

export async function POST(request) {
  try {
    const { url, text } = await request.json();
    if (!url) {
      return NextResponse.json({ success: false, error: 'URL is required' }, { status: 400 });
    }

    return new Promise((resolve) => {
      const workspaceRoot = process.cwd();
      const pythonPath = path.join(workspaceRoot, '.venv', 'bin', 'python');
      const scriptPath = path.join(workspaceRoot, 'scraper', 'scrape_single.py');
      
      const child = spawn(pythonPath, [scriptPath, url], {
        env: { ...process.env, PYTHONPATH: workspaceRoot }
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code !== 0) {
          console.error(`Scraper process exited with code ${code}. Stderr: ${stderr}`);
          resolve(NextResponse.json({ success: false, error: `Process exited with code ${code}`, details: stderr }, { status: 500 }));
          return;
        }

        try {
          // Filter out warning lines from python output (like NotOpenSSLWarning)
          const lines = stdout.trim().split('\n');
          const jsonLine = lines.find(line => line.trim().startsWith('{') && line.trim().endsWith('}'));
          
          if (!jsonLine) {
            console.error(`No JSON output found from scraper. Stdout: ${stdout}`);
            resolve(NextResponse.json({ success: false, error: 'Invalid response from scraper', details: stdout }, { status: 500 }));
            return;
          }

          const result = JSON.parse(jsonLine.trim());
          if (result.success) {
            resolve(NextResponse.json(result));
          } else {
            resolve(NextResponse.json(result, { status: 500 }));
          }
        } catch (e) {
          console.error(`Failed to parse Python output: ${stdout}, error: ${e.message}`);
          resolve(NextResponse.json({ success: false, error: 'Failed to parse scraper response', details: stdout }, { status: 500 }));
        }
      });

      if (text) {
        child.stdin.write(text);
      }
      child.stdin.end();
    });
  } catch (err) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
