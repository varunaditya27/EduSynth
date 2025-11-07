'use client';

interface StatusBadgeProps {
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colors = {
    pending: 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-500/30',
    processing: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 border-yellow-500/30',
    completed: 'bg-green-500/20 text-green-600 dark:text-green-400 border-green-500/30',
    failed: 'bg-red-500/20 text-red-600 dark:text-red-400 border-red-500/30',
  };

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${colors[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
