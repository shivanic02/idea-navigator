import React, { useState } from 'react';
import axios from 'axios';

export default function SummaryPanel() {
  const [summary, setSummary] = useState(null);

  const fetchSummary = async () => {
    const res = await axios.get('http://localhost:8000/summary');
    setSummary(res.data);
  };

  return (
    <div>
      <button onClick={fetchSummary}>📋 Show Final Summary</button>
      {summary && (
        <div>
          <h4>Summary</h4>
          <pre style={{ whiteSpace: 'pre-wrap', textAlign: 'left' }}>{JSON.stringify(summary, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
