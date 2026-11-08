#!/usr/bin/env node
// Contrôle SEO d'un export Next.js pour UN domaine. Échoue (code 1) en cas de régression.
// Usage : node scripts/check-seo.mjs <dossier-export> <fr|info|store>
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import { join, relative, sep } from 'node:path'

const ORIGINS = { fr: 'https://pulse-locale-pme.fr', info: 'https://pulse-locale-pme.info', store: 'https://pulse-locale-pme.store' }
const ownerOf = (p) => (p === '/info' || p.startsWith('/info/') ? 'info' : p === '/store' || p.startsWith('/store/') ? 'store' : 'fr')
// Pages hors SEO (non indexées, servies par d'autres routes, ou pages d'erreur).
const SKIP = [/^\/_next\//, /^\/app\//, /^\/espace\//, /^\/admin\//, /^\/404\//, /^\/_not-found\//]

const [outDir, site] = process.argv.slice(2)
if (!outDir || !ORIGINS[site]) { console.error('usage: check-seo.mjs <out> <fr|info|store>'); process.exit(2) }
const origin = ORIGINS[site]
const errors = []
const fail = (m) => errors.push(m)

function walk(dir) {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f)
    return statSync(p).isDirectory() ? walk(p) : [p]
  })
}
// Routes servies par l'API (Cloud Run) ou par le cockpit, absentes de l'export Next.
const DYNAMIC = [/^\/(app|buy|demo|preview|prospects|client|leads|photo)(\/|$)/]
function targetExists(dir, target) {
  if (DYNAMIC.some((r) => r.test(target))) return true
  const clean = target.endsWith('/') ? target : target + '/'
  if (existsSync(join(dir, clean, 'index.html'))) return true
  // Fichier (pas un dossier) : un dossier sans index.html n'est pas une page.
  return !target.endsWith('/') && existsSync(join(dir, target)) && !statSync(join(dir, target)).isDirectory()
}
const pathOf = (file) => '/' + relative(outDir, file).split(sep).join('/').replace(/index\.html$/, '')
const attr = (html, re) => (html.match(re) || [])[1]

// 1. Sitemap : uniquement des URL du domaine, chacune vers une page exportée dont la canonique est identique.
const sm = readFileSync(join(outDir, 'sitemap.xml'), 'utf8')
const locs = [...sm.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])
if (locs.length === 0) fail('sitemap.xml vide')
if (new Set(locs).size !== locs.length) fail('sitemap.xml contient des doublons')
if (!/<lastmod>\d{4}-\d{2}-\d{2}<\/lastmod>/.test(sm)) fail('sitemap.xml : lastmod absent ou non daté au jour')
for (const loc of locs) {
  if (!loc.startsWith(origin + '/')) { fail(`sitemap : ${loc} n'appartient pas à ${origin}`); continue }
  const p = loc.slice(origin.length)
  if (ownerOf(p) !== site) fail(`sitemap : ${p} appartient au domaine ${ownerOf(p)}, pas à ${site}`)
  const file = join(outDir, p, 'index.html')
  if (!existsSync(file)) { fail(`sitemap : ${loc} sans page exportée`); continue }
  const html = readFileSync(file, 'utf8')
  const can = attr(html, /<link rel="canonical" href="([^"]+)"/)
  if (can !== loc) fail(`sitemap : canonique de ${p} = ${can}, attendu ${loc}`)
  if (/<meta name="robots" content="[^"]*noindex/.test(html)) fail(`sitemap : ${p} est en noindex`)
}

// 2. robots.txt : pointe vers le sitemap du domaine et n'interdit pas le site public.
const robots = readFileSync(join(outDir, 'robots.txt'), 'utf8')
if (!robots.includes(`Sitemap: ${origin}/sitemap.xml`)) fail(`robots.txt : sitemap attendu ${origin}/sitemap.xml`)
if (/^Disallow: \/\s*$/m.test(robots)) fail('robots.txt : Disallow: / bloque tout le site')
for (const bot of ['Googlebot', 'Bingbot', 'OAI-SearchBot', 'PerplexityBot', 'Claude-SearchBot']) {
  if (!robots.includes(`User-Agent: ${bot}`)) fail(`robots.txt : ${bot} absent`)
}

// 3. Pages HTML possédées par ce domaine : canonique absolue correcte, title, description, un seul H1,
//    JSON-LD valide, liens internes relatifs uniquement vers des pages du même domaine.
const titles = new Map()
const pages = walk(outDir).filter((f) => f.endsWith('index.html')).map((f) => [pathOf(f), f]).filter(([p]) => !SKIP.some((r) => r.test(p)))
let checked = 0
for (const [p, file] of pages) {
  if (ownerOf(p) !== site) continue // copies servies par redirection 301 vers le bon domaine
  checked++
  const html = readFileSync(file, 'utf8')
  const can = attr(html, /<link rel="canonical" href="([^"]+)"/)
  if (!can) fail(`${p} : pas de canonique`)
  else if (can !== origin + p) fail(`${p} : canonique ${can}, attendu ${origin + p}`)
  const title = attr(html, /<title>([^<]*)<\/title>/)
  if (!title) fail(`${p} : <title> manquant`)
  else if (titles.has(title)) fail(`${p} : <title> identique à ${titles.get(title)}`)
  else titles.set(title, p)
  if (!/<meta name="description" content="[^"]{50,}"/.test(html)) fail(`${p} : meta description manquante ou trop courte`)
  if (!/<html lang="fr"/.test(html)) fail(`${p} : lang="fr" manquant`)
  if (!/property="og:url" content="https:\/\//.test(html)) fail(`${p} : og:url absolue manquante`)
  const h1 = (html.match(/<h1[\s>]/g) || []).length
  if (h1 !== 1) fail(`${p} : ${h1} H1 (attendu 1)`)
  for (const m of html.matchAll(/<script type="application\/ld\+json">(.*?)<\/script>/gs)) {
    try { JSON.parse(m[1]) } catch { fail(`${p} : JSON-LD invalide`) }
  }
  for (const m of html.matchAll(/<a [^>]*href="(\/[^"#?]*)/g)) {
    const target = m[1]
    if (/\.(pdf|png|svg|jpg|webp|txt|xml)$/.test(target)) {
      if (!existsSync(join(outDir, target))) fail(`${p} : fichier lié introuvable ${target}`)
      continue
    }
    if (ownerOf(target) !== site) { fail(`${p} : lien relatif ${target} vers le domaine ${ownerOf(target)} (doit être absolu)`); continue }
    if (!targetExists(outDir, target)) fail(`${p} : lien cassé ${target} (page absente de l'export)`)
  }
  for (const m of html.matchAll(/<a [^>]*href="(https:\/\/pulse-locale-pme\.(?:fr|info|store))(\/[^"#?]*)?/g)) {
    const target = m[2] || '/'
    const expected = ORIGINS[ownerOf(target)]
    if (m[1] !== expected) { fail(`${p} : lien ${m[1]}${target} pointe vers le mauvais domaine (attendu ${expected})`); continue }
    // Lien vers un autre domaine : vérifié si son export est disponible (scripts/build-sites.sh).
    const other = Object.keys(ORIGINS).find((k) => ORIGINS[k] === m[1])
    const otherOut = other === site ? outDir : join(outDir, '..', '..', 'hosting-dist', other)
    if (existsSync(otherOut) && !targetExists(otherOut, target)) fail(`${p} : lien cassé ${m[1]}${target}`)
  }
}
if (checked === 0) fail('aucune page du domaine trouvée')

// 4. Pages locales clés présentes sur le .fr.
if (site === 'fr') {
  for (const p of ['/', '/agence-seo-local-yvelines/', '/agence-seo-local-eure-et-loir/', '/methode/', '/a-propos/']) {
    if (!existsSync(join(outDir, p, 'index.html'))) fail(`page manquante : ${p}`)
  }
}

if (errors.length) {
  console.error(`✗ ${site} : ${errors.length} erreur(s)\n - ` + errors.join('\n - '))
  process.exit(1)
}
console.log(`✓ ${site} : ${checked} pages, ${locs.length} URL dans le sitemap, robots.txt conforme`)
