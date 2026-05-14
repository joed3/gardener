/** @type {import('next').NextConfig} */
const withPWA = (await import("next-pwa")).default({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
});

const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "upload.wikimedia.org" },
      { protocol: "https", hostname: "**.wikipedia.org" },
    ],
  },
};

export default withPWA(nextConfig);
