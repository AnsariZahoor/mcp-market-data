import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // Optimized for Docker
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "media.discordapp.net",
      },
    ],
  },
};

export default nextConfig;
