import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Allow cross-origin requests in development
  allowedDevOrigins: [
    "56.228.79.102",
    "suborbiculate-bruna-impleadable.ngrok-free.app",
  ],
  async headers() {
    return [
      {
        source: "/api/:path*",
        headers: [
          {
            key: "Access-Control-Allow-Origin",
            value: "https://suborbiculate-bruna-impleadable.ngrok-free.app",
          },
          {
            key: "Access-Control-Allow-Methods",
            value: "GET, POST, PUT, DELETE, OPTIONS",
          },
          {
            key: "Access-Control-Allow-Headers",
            value: "Content-Type, Authorization, X-Requested-With",
          },
          {
            key: "Access-Control-Allow-Credentials",
            value: "true",
          },
        ],
      },
      {
        source: "/_next/:path*",
        headers: [
          {
            key: "Access-Control-Allow-Origin",
            value: "https://suborbiculate-bruna-impleadable.ngrok-free.app",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
