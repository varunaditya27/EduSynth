import LectureForm from '@/components/forms/lecture-form';
import Iridescence from '@/components/Iridescence';
import SplashCursor from '@/components/SplashCursor';
import Navbar from '@/components/ui/navbar';

export default function GeneratorPage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Navbar variant="app" />
      <Iridescence
        color={[0.5, 0.7, 1]}
        speed={0.7}
        amplitude={0.5}
        mouseReact={true}
      />
      <SplashCursor
        SPLAT_FORCE={6000}
        DENSITY_DISSIPATION={3.5}
        VELOCITY_DISSIPATION={2}
        TRANSPARENT={true}
      />

      <div className="relative z-10 min-h-screen py-12 px-4 pt-24">
        <div className="max-w-4xl mx-auto">
          <div className="space-y-8">
            <div className="text-center space-y-4">
              <h1 className="text-5xl md:text-6xl font-bold gradient-text">
                Create Your Lecture
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Fill in the details below and let AI generate a complete lecture package with slides, voiceover, and quiz questions
              </p>
            </div>

            <div className="backdrop-blur-md bg-white/10 dark:bg-gray-900/50 border border-white/20 dark:border-white/10 rounded-xl p-8">
              <LectureForm />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
