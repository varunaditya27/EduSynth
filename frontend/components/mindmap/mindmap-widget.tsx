'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Brain, Loader2, Network } from 'lucide-react';
import MindmapViewer from './mindmap-viewer';
import { apiClient, MindMapResponse } from '@/lib/api';
import GradientButton from '../ui/gradient-button';

interface MindmapWidgetProps {
  lectureId: string;
  lectureTopic?: string;
  onMindmapGenerated?: (mindmap: MindMapResponse) => void;
  className?: string;
}

export default function MindmapWidget({
  lectureId,
  lectureTopic,
  onMindmapGenerated,
  className,
}: MindmapWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [mindmap, setMindmap] = useState<MindMapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasExistingMindmap, setHasExistingMindmap] = useState<boolean | null>(null);

  // Check if mindmap exists on component mount
  useEffect(() => {
    const checkExistingMindmap = async () => {
      try {
        const existing = await apiClient.getMindmapByLecture(lectureId);
        setMindmap(existing);
        setHasExistingMindmap(true);
      } catch (err: unknown) {
        if ((err as Error).message === 'MINDMAP_NOT_FOUND') {
          setHasExistingMindmap(false);
        }
      }
    };

    if (hasExistingMindmap === null) {
      checkExistingMindmap();
    }
  }, [lectureId, hasExistingMindmap]);

  const handleGenerateMindmap = async (regenerate = false) => {
    setLoading(true);
    setError(null);

    try {
      // If not regenerating and we already have a mindmap in state, just open it
      if (!regenerate && mindmap) {
        setIsOpen(true);
        setLoading(false);
        return;
      }

      // Call the generate endpoint directly
      const response = await apiClient.generateMindmap({
        lecture_id: lectureId,
        regenerate,
        max_branches: 6,
        max_depth: 3,
      });

      setMindmap(response);
      setHasExistingMindmap(true);
      setIsOpen(true);

      if (onMindmapGenerated) {
        onMindmapGenerated(response);
      }
    } catch (err: unknown) {
      console.error('Failed to generate mindmap:', err);
      const errorMessage = (err as Error).message || 'Failed to generate mindmap';
      
      // Handle case where mindmap already exists (409 Conflict)
      if (errorMessage.includes('already exists')) {
        try {
          // Fetch the existing mindmap
          const existing = await apiClient.getMindmapByLecture(lectureId);
          setMindmap(existing);
          setHasExistingMindmap(true);
          setIsOpen(true);
          if (onMindmapGenerated) {
            onMindmapGenerated(existing);
          }
        } catch {
          setError('Mindmap exists but could not be loaded');
        }
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOpenMindmap = async () => {
    // If already loaded in state, just open
    if (mindmap) {
      setIsOpen(true);
      return;
    }

    // Try to fetch existing mindmap
    setLoading(true);
    setError(null);

    try {
      const existing = await apiClient.getMindmapByLecture(lectureId);
      setMindmap(existing);
      setHasExistingMindmap(true);
      setIsOpen(true);
      if (onMindmapGenerated) {
        onMindmapGenerated(existing);
      }
    } catch (err: unknown) {
      setError((err as Error).message || 'Failed to load mindmap');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Trigger Button */}
      <GradientButton
        onClick={hasExistingMindmap ? handleOpenMindmap : () => handleGenerateMindmap(false)}
        disabled={loading}
        className={className}
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            {hasExistingMindmap ? 'Loading...' : 'Generating...'}
          </>
        ) : (
          <>
            <Network className="w-5 h-5 mr-2" />
            {hasExistingMindmap ? 'View Mindmap' : 'Generate Mindmap'}
          </>
        )}
      </GradientButton>

      {/* Error Display */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
        >
          {error}
        </motion.div>
      )}

      {/* Full-Screen Modal */}
      <AnimatePresence>
        {isOpen && mindmap && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-9999 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="relative w-[95vw] h-[95vh] bg-gray-900 rounded-2xl shadow-2xl border border-white/10 overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="absolute top-0 left-0 right-0 z-10 p-6 bg-linear-to-b from-gray-900 to-transparent">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-linear-to-br from-primary to-accent flex items-center justify-center">
                      <Brain className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-white">
                        {lectureTopic || 'Lecture Mindmap'}
                      </h2>
                      <p className="text-sm text-gray-400">
                        {mindmap.metadata.node_count} nodes • {mindmap.metadata.branch_count} branches
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <GradientButton
                      variant="secondary"
                      onClick={() => handleGenerateMindmap(true)}
                      disabled={loading}
                      className="text-sm"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Regenerating...
                        </>
                      ) : (
                        <>
                          <Network className="w-4 h-4 mr-2" />
                          Regenerate
                        </>
                      )}
                    </GradientButton>

                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => setIsOpen(false)}
                      className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors"
                    >
                      <X className="w-6 h-6 text-white" />
                    </motion.button>
                  </div>
                </div>
              </div>

              {/* Mindmap Viewer */}
              <div className="w-full h-full pt-24">
                <MindmapViewer mindmapData={mindmap.mind_map} />
              </div>

              {/* Footer Info */}
              <div className="absolute bottom-0 left-0 right-0 z-10 p-4 bg-linear-to-t from-gray-900 to-transparent">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <div>
                    <span className="font-semibold text-gray-300">Tip:</span> Use mouse wheel to zoom, drag to pan
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded-full bg-primary" />
                      Central
                    </span>
                    <span className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded-full bg-accent" />
                      Branches
                    </span>
                    <span className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded-full bg-pink-500" />
                      Concepts
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
