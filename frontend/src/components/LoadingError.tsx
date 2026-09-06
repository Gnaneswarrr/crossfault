import { AlertCircle, Terminal } from 'lucide-react';
import { motion } from 'framer-motion';

export function ErrorState({ error, onRetry }: { error: { status: number, message: string }, onRetry: () => void }) {
  return (
    <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', marginTop: '4rem' }}>
      <AlertCircle color="var(--color-failure)" size={48} style={{ margin: '0 auto 1rem' }} />
      <h2 style={{ color: 'var(--color-failure)', marginBottom: '1rem', letterSpacing: '0.1em' }}>
        API ERROR {error.status}
      </h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>{error.message}</p>
      <button className="run-button" onClick={onRetry}>RETRY CONNECTION</button>
    </div>
  );
}

export default function LoadingSkeleton() {
  return (
    <div className="glass-panel" style={{ padding: '4rem', marginTop: '4rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem' }}>
      <motion.div
        animate={{ opacity: [0.3, 1, 0.3] }}
        transition={{ repeat: Infinity, duration: 2 }}
      >
        <Terminal size={48} color="var(--text-secondary)" />
      </motion.div>
      <div style={{ textAlign: 'center' }}>
        <h2 style={{ letterSpacing: '0.1em', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          RUNNING BOUNDED REPLAY
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }} className="mono">
          Awaiting API response...
        </p>
      </div>
    </div>
  );
}
