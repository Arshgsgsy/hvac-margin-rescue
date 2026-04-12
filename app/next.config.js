const INTERNAL_API_URL = process.env.INTERNAL_API_URL || 'http://127.0.0.1:8000'
const PROXY_CLIENT_MAX_BODY_SIZE = process.env.PROXY_CLIENT_MAX_BODY_SIZE || '200mb'

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  experimental: {
    proxyClientMaxBodySize: PROXY_CLIENT_MAX_BODY_SIZE,
  },
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
