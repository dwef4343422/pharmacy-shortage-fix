/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Useful for Docker deployments
  experimental: {
    // any experimental features can go here
  }
};

module.exports = nextConfig;
