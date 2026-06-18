/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',       // génère landing-site/out/ → compatible Firebase Hosting
  trailingSlash: true,    // génère out/admin/index.html plutôt que out/admin.html
}
module.exports = nextConfig
