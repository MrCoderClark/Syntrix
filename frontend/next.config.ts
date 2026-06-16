import { resolve } from "path";
import type { NextConfig } from "next";
import { loadEnvConfig } from "@next/env";

loadEnvConfig(resolve(process.cwd(), ".."));

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8001";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: ["http://127.0.0.1:8001"],
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
