'use client';

import HeroSection from '@/components/sections/hero-section';
import FeatureGrid from '@/components/sections/feature-grid';
import PrismaticBurst from '@/components/PrismaticBurst';
import SplashCursor from '@/components/SplashCursor';
import Navbar from '@/components/ui/navbar';

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-black">
      <Navbar variant="landing" />
      
      {/* PrismaticBurst Background */}
      <div className="fixed inset-0 z-0">
        <PrismaticBurst
          intensity={1.8}
          speed={0.4}
          animationType="rotate3d"
          colors={[
            '#4169E1', // Royal Blue
            '#6A5ACD', // Slate Blue
            '#8A2BE2', // Blue Violet
            '#9370DB', // Medium Purple
            '#BA55D3', // Medium Orchid
            '#DA70D6', // Orchid
            '#EE82EE', // Violet
            '#FF69B4', // Hot Pink
            '#FF1493', // Deep Pink
          ]}
          distort={3}
          rayCount={12}
          mixBlendMode="lighten"
        />
      </div>

      <SplashCursor
        SPLAT_FORCE={7000}
        DENSITY_DISSIPATION={4}
        VELOCITY_DISSIPATION={2.5}
        TRANSPARENT={true}
      />
      
      <div className="relative z-10">
        <HeroSection />
        <FeatureGrid />
      </div>
    </div>
  );
}
