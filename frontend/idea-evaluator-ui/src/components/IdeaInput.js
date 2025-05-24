// import React, { useState } from 'react';
// import axios from 'axios';

// export default function IdeaInput() {
//   const [idea, setIdea] = useState('');
//   const [status, setStatus] = useState('');

//   const handleSubmit = async () => {
//     setStatus("⏳ Starting analysis...");
//     try {
//       const response = await axios.post('http://localhost:8000/start', { idea });
//       setStatus(response.data.message);
//     } catch (error) {
//       setStatus("❌ Failed to start analysis.");
//     }
//   };

//   return (
//     <div style={{ margin: '20px 0' }}>
//       <textarea
//         rows="4"
//         cols="60"
//         value={idea}
//         placeholder="💡 Describe your startup idea..."
//         onChange={(e) => setIdea(e.target.value)}
//         style={{ padding: '10px' }}
//       />
//       <br />
//       <button onClick={handleSubmit}>Start Evaluation</button>
//       <p>{status}</p>
//     </div>
//   );
// }



// working ui


// import React, { useState } from 'react';
// import axios from 'axios';

// export default function IdeaInput() {
//   const [idea, setIdea] = useState('');
//   const [initialUserInput, setInitialUserInput] = useState(
//     "The core problem this solves is the high failure rate of startups due to unvalidated ideas and lack of strategic direction. Focus the opportunity analysis on the market of aspiring and early-stage entrepreneurs seeking quick, affordable, and data-driven feedback before committing significant resources. Consider current trends in AI adoption by small businesses."
//   );
//   const [statusMessage, setStatusMessage] = useState('Ready to start evaluation.');
//   const [isLoading, setIsLoading] = useState(false);
//   const [sessionId, setSessionId] = useState(null); // Store the session ID from /start
//   const [analysisResults, setAnalysisResults] = useState(null); // Store the full analysis results
//   const [overallSystemStatus, setOverallSystemStatus] = useState(null); // For fetching overall status

//   const API_BASE_URL = 'http://localhost:8000'; // Define your API base URL

//   const handleStartSession = async () => {
//     setIsLoading(true);
//     setAnalysisResults(null); // Clear previous results
//     setOverallSystemStatus(null);
//     setStatusMessage("⏳ Starting analysis session...");
//     try {
//       const response = await axios.post(`${API_BASE_URL}/start`, { idea });
//       setStatusMessage(response.data.message);
//       setSessionId(response.data.session_id); // Store the session ID
//       console.log("Session started:", response.data);
//     } catch (error) {
//       console.error("Error starting session:", error.response?.data || error.message);
//       setStatusMessage(`❌ Failed to start analysis session: ${error.response?.data?.error || error.message}`);
//       setSessionId(null);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const handleRunFullAnalysis = async () => {
//     if (!sessionId) {
//       setStatusMessage("Please start a session first!");
//       return;
//     }

//     setIsLoading(true);
//     setAnalysisResults(null); // Clear previous results
//     setStatusMessage("🚀 Running full sequential analysis... This may take several minutes.");
//     try {
//       // Call /analyze without a 'layer' to trigger full sequential analysis
//       const response = await axios.post(`${API_BASE_URL}/analyze`, {
//         user_input: initialUserInput
//       });
//       setAnalysisResults(response.data);
//       if (response.data.error) {
//         setStatusMessage(`❌ Analysis failed: ${response.data.error}`);
//       } else {
//         setStatusMessage("✅ Full analysis completed!");
//       }
//       console.log("Full analysis results:", response.data);
//       // Automatically fetch overall status after analysis
//       await fetchOverallSystemStatus();

//     } catch (error) {
//       console.error("Error running full analysis:", error.response?.data || error.message);
//       setStatusMessage(`❌ Failed to run full analysis: ${error.response?.data?.error || error.message}`);
//       setAnalysisResults(null);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const fetchOverallSystemStatus = async () => {
//     try {
//       const response = await axios.get(`${API_BASE_URL}/status`);
//       setOverallSystemStatus(response.data);
//       console.log("Overall System Status:", response.data);
//     } catch (error) {
//       console.error("Error fetching system status:", error.response?.data || error.message);
//       setOverallSystemStatus({ error: `Failed to fetch status: ${error.response?.data?.error || error.message}` });
//     }
//   };


//   const renderLayerDetails = (details) => {
//     if (!details || details.length === 0) {
//       return <p>No detailed layer results available.</p>;
//     }

//     return (
//       <div style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px', marginTop: '20px', backgroundColor: '#f9f9f9' }}>
//         <h3>Detailed Layer Results:</h3>
//         {details.map((layer, index) => (
//           <div key={layer.layer || index} style={{ marginBottom: '15px', paddingBottom: '10px', borderBottom: '1px dashed #eee' }}>
//             <h4>{layer.name} (Layer {layer.layer}) - Status: <span style={{ color: layer.status === 'COMPLETED' ? 'green' : (layer.status.includes('SKIPPED') ? 'orange' : 'red') }}>{layer.status}</span></h4>
//             {layer.confidence && <p><strong>Confidence:</strong> {layer.confidence}</p>}
//             {layer.error && <p style={{ color: 'red' }}><strong>Error:</strong> {layer.error}</p>}
//             {layer.reason && <p><strong>Reason:</strong> {layer.reason}</p>}
//             {layer.analysis_snippet && (
//               <p>
//                 <strong>Analysis Snippet:</strong> <span style={{ whiteSpace: 'pre-wrap' }}>{layer.analysis_snippet}</span>
//               </p>
//             )}
//           </div>
//         ))}
//       </div>
//     );
//   };

//   return (
//     <div style={{ fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '30px auto', padding: '20px', border: '1px solid #eee', borderRadius: '10px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
//       <h2 style={{ textAlign: 'center', color: '#333' }}>💡 Idea Evaluation System (Claude Demo)</h2>

//       <div style={{ marginBottom: '20px' }}>
//         <h3>1. Describe Your Idea:</h3>
//         <textarea
//           rows="5"
//           cols="80"
//           value={idea}
//           placeholder="e.g., A Gen AI application that automates startup idea validation by performing real-time market research..."
//           onChange={(e) => setIdea(e.target.value)}
//           style={{ padding: '10px', width: '100%', borderRadius: '5px', border: '1px solid #ddd' }}
//           disabled={isLoading}
//         />
//         <br />
//         <button
//           onClick={handleStartSession}
//           disabled={isLoading || !idea.trim()}
//           style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '16px', marginTop: '10px' }}
//         >
//           {isLoading && !sessionId ? 'Starting...' : 'Start New Evaluation Session'}
//         </button>
//       </div>

//       <p style={{ margin: '15px 0', fontSize: '1.1em', fontWeight: 'bold', color: isLoading ? '#007bff' : '#333' }}>Status: {statusMessage}</p>

//       {sessionId && (
//         <div style={{ marginTop: '30px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
//           <h3>2. Provide Initial Input for Layer 1 (Optional):</h3>
//           <p style={{ fontSize: '0.9em', color: '#666' }}>This input helps guide the first layer of analysis.</p>
//           <textarea
//             rows="5"
//             cols="80"
//             value={initialUserInput}
//             placeholder="e.g., The core problem this solves is..."
//             onChange={(e) => setInitialUserInput(e.target.value)}
//             style={{ padding: '10px', width: '100%', borderRadius: '5px', border: '1px solid #ddd' }}
//             disabled={isLoading}
//           />
//           <br />
//           <button
//             onClick={handleRunFullAnalysis}
//             disabled={isLoading}
//             style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '16px', marginTop: '10px' }}
//           >
//             {isLoading && sessionId ? 'Running Full Analysis...' : 'Run Full Sequential Analysis'}
//           </button>
//           <button
//             onClick={() => {
//               setIdea('');
//               setStatusMessage('Ready to start evaluation.');
//               setIsLoading(false);
//               setSessionId(null);
//               setAnalysisResults(null);
//               setOverallSystemStatus(null);
//             }}
//             disabled={isLoading}
//             style={{ padding: '10px 20px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '16px', marginTop: '10px', marginLeft: '10px' }}
//           >
//             Reset All
//           </button>
//         </div>
//       )}

//       {analysisResults && analysisResults.detailed_layer_summary && (
//         renderLayerDetails(analysisResults.detailed_layer_summary)
//       )}

//       {overallSystemStatus && (
//         <div style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px', marginTop: '20px', backgroundColor: '#f0f0f0' }}>
//             <h3>Overall System Status:</h3>
//             <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.9em' }}>
//                 {JSON.stringify(overallSystemStatus, null, 2)}
//             </pre>
//         </div>
//       )}

//       {analysisResults && analysisResults.error && (
//         <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#ffe0e0', border: '1px solid #ff4d4d', borderRadius: '8px' }}>
//           <h3>Analysis Error:</h3>
//           <p style={{ color: 'red' }}>{analysisResults.error}</p>
//         </div>
//       )}
//     </div>
//   );
// }









import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown'; // Import ReactMarkdown
import remarkGfm from 'remark-gfm';       // Import remarkGfm for GitHub Flavored Markdown

export default function IdeaInput() {
  const [idea, setIdea] = useState('');
  const [initialUserInput, setInitialUserInput] = useState(
    "The core problem this solves is the high failure rate of startups due to unvalidated ideas and lack of strategic direction. Focus the opportunity analysis on the market of aspiring and early-stage entrepreneurs seeking quick, affordable, and data-driven feedback before committing significant resources. Consider current trends in AI adoption by small businesses."
  );
  const [statusMessage, setStatusMessage] = useState('Ready to start evaluation.');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null); // Store the session ID from /start
  const [analysisResults, setAnalysisResults] = useState(null); // Store the full analysis results
  const [overallSystemStatus, setOverallSystemStatus] = useState(null); // For fetching overall status

  const API_BASE_URL = 'http://localhost:8000'; // Define your API base URL

  const handleStartSession = async () => {
    setIsLoading(true);
    setAnalysisResults(null); // Clear previous results
    setOverallSystemStatus(null);
    setStatusMessage("⏳ Starting analysis session...");
    try {
      const response = await axios.post(`${API_BASE_URL}/start`, { idea });
      setStatusMessage(response.data.message);
      setSessionId(response.data.session_id); // Store the session ID
      console.log("Session started:", response.data);
    } catch (error) {
      console.error("Error starting session:", error.response?.data || error.message);
      setStatusMessage(`❌ Failed to start analysis session: ${error.response?.data?.error || error.message}`);
      setSessionId(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunFullAnalysis = async () => {
    if (!sessionId) {
      setStatusMessage("Please start a session first!");
      return;
    }

    setIsLoading(true);
    setAnalysisResults(null); // Clear previous results
    setStatusMessage("🚀 Running full sequential analysis... This may take several minutes.");
    try {
      // Call /analyze without a 'layer' to trigger full sequential analysis
      const response = await axios.post(`${API_BASE_URL}/analyze`, {
        user_input: initialUserInput
      });
      setAnalysisResults(response.data);
      if (response.data.error) {
        setStatusMessage(`❌ Analysis failed: ${response.data.error}`);
      } else {
        setStatusMessage("✅ Full analysis completed!");
      }
      console.log("Full analysis results:", response.data);
      // Automatically fetch overall status after analysis
      await fetchOverallSystemStatus();

    } catch (error) {
      console.error("Error running full analysis:", error.response?.data || error.message);
      setStatusMessage(`❌ Failed to run full analysis: ${error.response?.data?.error || error.message}`);
      setAnalysisResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchOverallSystemStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status`);
      setOverallSystemStatus(response.data);
      console.log("Overall System Status:", response.data);
    } catch (error) {
      console.error("Error fetching system status:", error.response?.data || error.message);
      setOverallSystemStatus({ error: `Failed to fetch status: ${error.response?.data?.error || error.message}` });
    }
  };


  const renderLayerDetails = (details) => {
    if (!details || details.length === 0) {
      return <p>No detailed layer results available.</p>;
    }

    return (
      <div style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px', marginTop: '20px', backgroundColor: '#f9f9f9' }}>
        <h3>Detailed Layer Results:</h3>
        {details.map((layer, index) => (
          <div key={layer.layer || index} style={{ marginBottom: '15px', paddingBottom: '10px', borderBottom: '1px dashed #eee' }}>
            <h4>{layer.name} (Layer {layer.layer}) - Status: <span style={{ color: layer.status === 'COMPLETED' ? 'green' : (layer.status.includes('SKIPPED') ? 'orange' : 'red') }}>{layer.status}</span></h4>
            {layer.confidence && <p><strong>Confidence:</strong> {layer.confidence}</p>}
            {layer.error && <p style={{ color: 'red' }}><strong>Error:</strong> {layer.error}</p>}
            {layer.reason && <p><strong>Reason:</strong> {layer.reason}</p>}
            {layer.analysis_text && ( // Changed from analysis_snippet to analysis_text
              <div style={{ marginTop: '10px' }}>
                <strong>Full Analysis:</strong>
                <div style={{
                  border: '1px dashed #ddd',
                  padding: '10px',
                  marginTop: '5px',
                  backgroundColor: '#fff',
                  borderRadius: '5px',
                  maxHeight: '300px', // Added for scrollable long texts
                  overflowY: 'auto'   // Added for scrollable long texts
                }}>
                  {/* Use ReactMarkdown to render the full text */}
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {layer.analysis_text}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '30px auto', padding: '20px', border: '1px solid #eee', borderRadius: '10px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
      <h2 style={{ textAlign: 'center', color: '#333' }}>💡 Idea Evaluation System (Claude Demo)</h2>

      <div style={{ marginBottom: '20px' }}>
        <h3>1. Describe Your Idea:</h3>
        <textarea
          rows="5"
          cols="80"
          value={idea}
          placeholder="e.g., A Gen AI application that automates startup idea validation by performing real-time market research..."
          onChange={(e) => setIdea(e.target.value)}
          style={{ padding: '10px', width: '100%', borderRadius: '5px', border: '1px solid #ddd' }}
          disabled={isLoading}
        />
        <br />
        <button
          onClick={handleStartSession}
          disabled={isLoading || !idea.trim()}
          style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '16px', marginTop: '10px' }}
        >
          {isLoading && !sessionId ? 'Starting...' : 'Start New Evaluation Session'}
        </button>
      </div>

      <p style={{ margin: '15px 0', fontSize: '1.1em', fontWeight: 'bold', color: isLoading ? '#007bff' : '#333' }}>Status: {statusMessage}</p>

      {sessionId && (
        <div style={{ marginTop: '30px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
          <h3>2. Provide Initial Input for Layer 1 (Optional):</h3>
          <p style={{ fontSize: '0.9em', color: '#666' }}>This input helps guide the first layer of analysis.</p>
          <textarea
            rows="5"
            cols="80"
            value={initialUserInput}
            placeholder="e.g., The core problem this solves is..."
            onChange={(e) => setInitialUserInput(e.target.value)}
            style={{ padding: '10px', width: '100%', borderRadius: '5px', border: '1px solid #ddd' }}
            disabled={isLoading}
          />
          <br />
          <button
            onClick={handleRunFullAnalysis}
            disabled={isLoading}
            style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '16px', marginTop: '10px' }}
          >
            {isLoading && sessionId ? 'Running Full Analysis...' : 'Run Full Sequential Analysis'}
          </button>
          <button
            onClick={() => {
              setIdea('');
              setStatusMessage('Ready to start evaluation.');
              setIsLoading(false);
              setSessionId(null);
              setAnalysisResults(null);
              setOverallSystemStatus(null);
            }}
            disabled={isLoading}
            style={{ padding: '10px 20px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '16px', marginTop: '10px', marginLeft: '10px' }}
          >
            Reset All
          </button>
        </div>
      )}

      {analysisResults && analysisResults.detailed_layer_summary && (
        renderLayerDetails(analysisResults.detailed_layer_summary)
      )}

      {overallSystemStatus && (
        <div style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px', marginTop: '20px', backgroundColor: '#f0f0f0' }}>
            <h3>Overall System Status:</h3>
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.9em' }}>
                {JSON.stringify(overallSystemStatus, null, 2)}
            </pre>
        </div>
      )}

      {analysisResults && analysisResults.error && (
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#ffe0e0', border: '1px solid #ff4d4d', borderRadius: '8px' }}>
          <h3>Analysis Error:</h3>
          <p style={{ color: 'red' }}>{analysisResults.error}</p>
        </div>
      )}
    </div>
  );
}