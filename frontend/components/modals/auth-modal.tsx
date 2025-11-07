'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SpotlightCard from '@/components/SpotlightCard';
import StarBorder from '@/components/StarBorder';
import { X, Mail, Lock, User, Chrome, AlertCircle } from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';
import LoadingDots from '@/components/ui/loading-dots';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultMode?: 'login' | 'signup';
}

export default function AuthModal({ isOpen, onClose, defaultMode = 'login' }: AuthModalProps) {
  const { login, signup, loginWithGoogle } = useAuth();
  const [mode, setMode] = useState<'login' | 'signup'>(defaultMode);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'signup') {
        await signup(formData.name, formData.email, formData.password);
      } else {
        await login(formData.email, formData.password);
      }
      
      // Close modal on success
      onClose();
      
      // Reset form
      setFormData({ name: '', email: '', password: '' });
    } catch (err: unknown) {
      console.error('Auth error:', err);
      setError((err as Error).message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    setError('Google OAuth not yet implemented. Please use email/password.');
    // TODO: Implement Google OAuth
    // The flow would be:
    // 1. Open Google OAuth popup
    // 2. Get ID token from Google
    // 3. Call loginWithGoogle(idToken)
    // 4. Close modal on success
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-99999 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
        style={{ 
          overflowY: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh'
        }}
        onClick={(e) => {
          // Only close if clicking the backdrop, not the modal content
          if (e.target === e.currentTarget) {
            onClose();
          }
        }}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          transition={{ type: 'spring', duration: 0.5 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-md relative my-auto"
          style={{ margin: 'auto' }}
        >
          {/* Close button - Outside SpotlightCard for better visibility */}
          <button
            onClick={onClose}
            className="absolute -top-4 -right-4 z-100000 p-2 rounded-full bg-red-500/80 hover:bg-red-500 transition-all shadow-lg hover:shadow-red-500/50 hover:scale-110"
          >
            <X className="w-5 h-5 text-white" />
          </button>

          <SpotlightCard
            spotlightColor="rgba(138, 43, 226, 0.25)"
            className="relative"
          >

            <div className="p-8 space-y-6">
              {/* Header */}
              <div className="text-center space-y-2">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring' }}
                  className="inline-block p-3 rounded-2xl bg-linear-to-br from-blue-500 to-purple-500"
                >
                </motion.div>
                <h2 className="text-3xl font-bold gradient-text">
                  {mode === 'login' ? 'Welcome Back' : 'Join EduSynth'}
                </h2>
                <p className="text-white/60">
                  {mode === 'login'
                    ? 'Sign in to continue creating amazing lectures'
                    : 'Start creating professional lectures with AI'}
                </p>
              </div>

              {/* Google Sign In */}
              <StarBorder
                as="button"
                type="button"
                color="rgba(66, 133, 244, 0.8)"
                speed="4s"
                thickness={2}
                className="w-full"
                onClick={handleGoogleLogin}
                disabled={loading}
              >
                <motion.div
                  whileHover={{ scale: loading ? 1 : 1.02 }}
                  whileTap={{ scale: loading ? 1 : 0.98 }}
                  className="flex items-center justify-center gap-3 px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                >
                  <Chrome className="w-5 h-5 text-white" />
                  <span className="font-semibold text-white">
                    Continue with Google
                  </span>
                </motion.div>
              </StarBorder>

              {/* Error Message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
                >
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </motion.div>
              )}

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/10"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-transparent text-white/50">Or continue with email</span>
                </div>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {mode === 'signup' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <label className="block text-sm font-medium text-white/70 mb-2">
                      Full Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="w-full pl-11 pr-4 py-3 rounded-lg bg-white/5 border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-white placeholder:text-white/30 transition-all"
                        placeholder="John Doe"
                        required={mode === 'signup'}
                      />
                    </div>
                  </motion.div>
                )}

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full pl-11 pr-4 py-3 rounded-lg bg-white/5 border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-white placeholder:text-white/30 transition-all"
                      placeholder="you@example.com"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full pl-11 pr-4 py-3 rounded-lg bg-white/5 border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-white placeholder:text-white/30 transition-all"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </div>

                {mode === 'login' && (
                  <div className="flex items-center justify-between text-sm">
                    <label className="flex items-center gap-2 text-white/60 cursor-pointer">
                      <input
                        type="checkbox"
                        className="w-4 h-4 rounded border-white/20 bg-white/5 text-primary focus:ring-primary/20"
                      />
                      Remember me
                    </label>
                    <button
                      type="button"
                      className="text-primary hover:text-primary/80 transition-colors"
                    >
                      Forgot password?
                    </button>
                  </div>
                )}

                <StarBorder
                  as="button"
                  type="submit"
                  color="rgba(138, 43, 226, 0.9)"
                  speed="3s"
                  thickness={2}
                  className="w-full"
                  disabled={loading}
                >
                  <motion.div
                    whileHover={{ scale: loading ? 1 : 1.02 }}
                    whileTap={{ scale: loading ? 1 : 0.98 }}
                    className="px-6 py-3 rounded-lg bg-linear-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all font-semibold text-white"
                  >
                    {loading ? (
                      <LoadingDots />
                    ) : (
                      mode === 'login' ? 'Sign In' : 'Create Account'
                    )}
                  </motion.div>
                </StarBorder>
              </form>

              {/* Toggle mode */}
              <div className="text-center text-sm text-white/60">
                {mode === 'login' ? (
                  <>
                    Don&apos;t have an account?{' '}
                    <button
                      onClick={() => setMode('signup')}
                      className="text-primary hover:text-primary/80 font-semibold transition-colors"
                    >
                      Sign up
                    </button>
                  </>
                ) : (
                  <>
                    Already have an account?{' '}
                    <button
                      onClick={() => setMode('login')}
                      className="text-primary hover:text-primary/80 font-semibold transition-colors"
                    >
                      Sign in
                    </button>
                  </>
                )}
              </div>

              {/* Terms */}
              {mode === 'signup' && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-xs text-center text-white/40"
                >
                  By signing up, you agree to our{' '}
                  <a href="#" className="text-primary hover:underline">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a href="#" className="text-primary hover:underline">
                    Privacy Policy
                  </a>
                </motion.p>
              )}
            </div>
          </SpotlightCard>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
