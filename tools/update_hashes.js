const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function updateManifest(manifestPath, baseDir) {
  if (!fs.existsSync(manifestPath)) return;
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.built_utc = new Date().toISOString();
  
  for (const relPath of Object.keys(manifest.files)) {
    const fullPath = path.join(baseDir, relPath.replace(/\//g, path.sep));
    if (fs.existsSync(fullPath)) {
      const buf = fs.readFileSync(fullPath);
      const hash = crypto.createHash('sha256').update(buf).digest('hex');
      manifest.files[relPath] = hash;
    } else {
      console.warn('File not found for hash:', fullPath);
    }
  }
  
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 4), 'utf8');
  console.log('Updated manifest:', manifestPath);
}

updateManifest('SHA256.json', '.');
updateManifest('Tawreed.org/SHA256.json', 'Tawreed.org');
