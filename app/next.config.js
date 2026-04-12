const INTERNAL_API_URL = process.env.INTERNAL_API_URL || 'http://127.0.0.1:8000'

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${INTERNAL_API_URL}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
