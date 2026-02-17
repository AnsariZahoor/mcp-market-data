"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to login - this app is just an OAuth login gateway
    router.push("/login");
  }, [router]);

  return (
    <div className="loading-screen">
      <p>Redirecting to login...</p>
    </div>
  );
}
