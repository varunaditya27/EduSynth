import HeroSection from '@/components/sections/hero-section';
import FeatureGrid from '@/components/sections/feature-grid';
import Iridescence from '@/components/Iridescence';
import SplashCursor from '@/components/SplashCursor';

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Iridescence
        color={[0.4, 0.6, 1]}
        speed={1.0}
        amplitude={2.0}
        mouseReact={true}
      />
      <SplashCursor
        SPLAT_FORCE={9000}
        DENSITY_DISSIPATION={3.5}
        VELOCITY_DISSIPATION={2}
        TRANSPARENT={true}
      />
      <div className="relative z-10">
        <HeroSection />
        <FeatureGrid />
      </div>
    </div>
  );
}
