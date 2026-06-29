export default function StatusPill({ status }) {
  const statusConfig = {
    checking: { text: 'Checking...', bg: '#374151', color: '#9ca3af' },
    connected: { text: 'API Connected', bg: '#064e3b', color: '#34d399' },
    offline: { text: 'API Offline', bg: '#7f1d1d', color: '#f87171' },
  };

  const config = statusConfig[status] || statusConfig.checking;

  return (
    <div
      className="status-pill"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '4px 10px',
        borderRadius: '4px',
        backgroundColor: config.bg,
        color: config.color,
        fontSize: '12px',
        fontFamily: 'Inter, sans-serif',
        fontWeight: '500',
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: config.color,
        }}
      />
      {config.text}
    </div>
  );
}
