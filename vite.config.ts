import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { execSync } from 'child_process'

// Derive version from git: 1.0.<commit-count>-<short-hash>
// Increments automatically on every commit. No manual bumping.
function getGitVersion(): string {
  try {
    const count = execSync('git rev-list --count HEAD', { encoding: 'utf-8' }).trim();
    const hash = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim();
    return `1.0.${count}-${hash}`;
  } catch {
    return '0.0.0-unknown';
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    '__APP_VERSION__': JSON.stringify(getGitVersion()),
  },
})
