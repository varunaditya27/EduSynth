import React from 'react';
import { FileText, Download, BookOpen, Layout, Palette, FileCheck } from 'lucide-react';

interface PDFStatusCardProps {
  status: 'idle' | 'generating' | 'ready' | 'error';
  pdfUrl?: string | null;
  error?: string | null;
  theme?: string;
  devicePreset?: string;
}

export default function PDFStatusCard({
  status,
  pdfUrl,
  error,
  theme = 'minimalist',
  devicePreset = 'desktop',
}: PDFStatusCardProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'generating':
        return {
          icon: FileText,
          title: 'Generating Lecture Notes',
          description: 'Creating comprehensive PDF with diagrams and key concepts',
          color: 'blue',
          animate: true,
        };
      case 'ready':
        return {
          icon: FileCheck,
          title: 'PDF Ready',
          description: 'Your lecture notes are ready to download',
          color: 'green',
          animate: false,
        };
      case 'error':
        return {
          icon: FileText,
          title: 'PDF Generation Failed',
          description: error || 'Unable to generate PDF notes',
          color: 'red',
          animate: false,
        };
      default:
        return {
          icon: FileText,
          title: 'Preparing PDF',
          description: 'Initializing document generation',
          color: 'gray',
          animate: false,
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const colorClasses = {
    blue: {
      bg: 'bg-blue-500/20',
      border: 'border-blue-500/30',
      text: 'text-blue-400',
      button: 'bg-blue-500 hover:bg-blue-600',
    },
    green: {
      bg: 'bg-green-500/20',
      border: 'border-green-500/30',
      text: 'text-green-400',
      button: 'bg-green-500 hover:bg-green-600',
    },
    red: {
      bg: 'bg-red-500/20',
      border: 'border-red-500/30',
      text: 'text-red-400',
      button: 'bg-red-500 hover:bg-red-600',
    },
    gray: {
      bg: 'bg-gray-500/20',
      border: 'border-gray-500/30',
      text: 'text-gray-400',
      button: 'bg-gray-500 hover:bg-gray-600',
    },
  };

  const colors = colorClasses[config.color as keyof typeof colorClasses];

  return (
    <div className="backdrop-blur-md bg-white/10 dark:bg-gray-900/50 border border-white/20 dark:border-white/10 rounded-xl p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${colors.bg} border ${colors.border}`}>
            <Icon className={`w-6 h-6 ${colors.text} ${config.animate ? 'animate-pulse' : ''}`} />
          </div>
          <div className="text-left">
            <h4 className="font-semibold text-base">{config.title}</h4>
            <p className="text-sm text-muted-foreground">{config.description}</p>
          </div>
        </div>
        <div>
          {status === 'ready' && pdfUrl && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`flex items-center gap-2 px-4 py-2 ${colors.button} text-white rounded-lg transition-colors shadow-lg`}
            >
              <Download className="w-4 h-4" />
              Download
            </a>
          )}
        </div>
      </div>

      {/* Features */}
      {(status === 'generating' || status === 'ready') && (
        <div className="grid grid-cols-3 gap-3 pt-2 border-t border-white/10">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Palette className="w-4 h-4" />
            <span className="capitalize">{theme}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Layout className="w-4 h-4" />
            <span className="capitalize">{devicePreset}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <BookOpen className="w-4 h-4" />
            <span>A4 Format</span>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {status === 'generating' && (
        <div className="w-full h-1 bg-gray-700 rounded-full overflow-hidden">
          <div className="h-full bg-blue-500 animate-pulse" style={{ width: '60%' }} />
        </div>
      )}
    </div>
  );
}
