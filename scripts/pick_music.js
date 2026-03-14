#!/usr/bin/env node
/**
 * Pick a background music track from the music mapping json.
 *
 * Priority (GitHub-friendly):
 *   1) assets/audio/music.local.json  (your full local library; NOT committed)
 *   2) assets/audio/music.sample.json (ships with this repo)
 *   3) assets/audio/music.json        (legacy/back-compat)
 *
 * Usage:
 *   node scripts/pick_music.js --label "大自然河流"
 *   node scripts/pick_music.js --goal  "助眠" --seed "2026-03-14"
 *
 * Output (stdout): absolute path to chosen mp3
 */

const fs = require('fs');
const path = require('path');

function arg(name) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

function hashSeed(s) {
  // simple deterministic hash
  let h = 2166136261;
  for (const ch of String(s)) {
    h ^= ch.charCodeAt(0);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0);
}

const label = arg('label');
const goal = arg('goal');
const seed = arg('seed') || new Date().toISOString().slice(0, 10);

const root = path.resolve(__dirname, '..');
const audioDir = path.join(root, 'assets', 'audio');
function firstExisting(paths) {
  for (const p of paths) {
    if (fs.existsSync(p)) return p;
  }
  return null;
}

const musicJsonPath = firstExisting([
  path.join(audioDir, 'music.local.json'),
  path.join(audioDir, 'music.sample.json'),
  path.join(audioDir, 'music.json')
]);

if (!musicJsonPath) {
  console.error('No music mapping file found. Expected one of: music.local.json / music.sample.json / music.json');
  process.exit(2);
}

const data = JSON.parse(fs.readFileSync(musicJsonPath, 'utf8'));
const list = Array.isArray(data.music) ? data.music : [];

const goalToLabels = {
  '助眠': ['大自然海浪', '冬日篝火', '大自然下雨', '空灵人声'],
  '减压': ['大自然河流', '大自然森林', '温和乐器', '电子氛围'],
  '焦虑': ['大自然河流', '温和乐器', '电子氛围'],
  '专注': ['温和乐器', '电子氛围'],
  '静心': ['大自然森林', '温和乐器', '大自然河流']
};

let candidates = list;
if (label) {
  candidates = list.filter(x => x.label === label);
} else if (goal && goalToLabels[goal]) {
  const labels = new Set(goalToLabels[goal]);
  candidates = list.filter(x => labels.has(x.label));
}

if (!candidates.length) {
  candidates = list;
}

if (!candidates.length) {
  console.error('No tracks in music.json');
  process.exit(2);
}

const h = hashSeed(seed + '|' + (label || '') + '|' + (goal || ''));
const chosen = candidates[h % candidates.length];

const abs = path.join(audioDir, chosen.file_name);
process.stdout.write(abs);
