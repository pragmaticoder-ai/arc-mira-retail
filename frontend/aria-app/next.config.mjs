/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  distDir: process.env.ARC_NEXT_DIST_DIR || '.next',
  typescript: { tsconfigPath: process.env.ARC_TSCONFIG_PATH || 'tsconfig.json' },
}

export default nextConfig
