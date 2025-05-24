import React, { useState } from 'react';
import axios from 'axios';

export default function LayerResults() {
  const [layer, setLayer] = useState(1);
  const [result, setResult] = useState(null);

  const runLayer = async () => {
    try {
      const response = await axios.post('http://localhost:8000/analyze', { layer });
      setResult(response.data);
    } catch (error) {
      setResult({ error: "Layer analysis failed" });
    }
  };

  return (
    <div>
      <h3>Run Analysis Layer</h3>
      <select onChange={(e) => setLayer(parseInt(e.target.value))} value={layer}>
        {[1, 2, 3, 4, 5].map((l) => (
          <option key={l} value={l}>Layer {l}</option>
        ))}
      </select>
      <button onClick={runLayer}>Analyze</button>
      {result && (
        <div>
          <h4>Layer {layer} Result:</h4>
          <pre style={{ whiteSpace: 'pre-wrap', textAlign: 'left' }}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
