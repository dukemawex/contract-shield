'use client';

import { useState } from 'react';

interface RedFlag {
  title: string;
  severity: string;
  explanation: string;
  negotiation_tip: string;
}

interface AnalysisResult {
  risk_score: number;
  red_flags: RedFlag[];
  negotiation_tips: string[];
  draft_email: string;
  summary: string;
  text_length: number;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 70) return 'text-red-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getRiskLabel = (score: number) => {
    if (score >= 70) return 'High Risk';
    if (score >= 40) return 'Medium Risk';
    return 'Low Risk';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default: return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">🛡️ Contract Shield</h1>
          <p className="text-gray-600">AI-powered contract risk analysis for freelancers</p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Contract (PDF or DOCX)
              </label>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
            </div>
            
            <button
              type="submit"
              disabled={!file || loading}
              className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Analyzing...' : 'Analyze Contract'}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}
        </div>

        {result && (
          <div className="space-y-6">
            {/* Risk Score */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold mb-4">Risk Assessment</h2>
              <div className="flex items-center justify-center">
                <div className="text-center">
                  <div className={`text-6xl font-bold ${getRiskColor(result.risk_score)}`}>
                    {result.risk_score}
                  </div>
                  <div className="text-gray-600 mt-2">{getRiskLabel(result.risk_score)}</div>
                </div>
              </div>
            </div>

            {/* Contract Summary */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold mb-4">Contract Summary</h2>
              <p className="text-gray-700 leading-relaxed">{result.summary}</p>
              <p className="text-sm text-gray-500 mt-2">
                Total text length: {result.text_length.toLocaleString()} characters
              </p>
            </div>

            {/* Red Flags */}
            {result.red_flags.length > 0 && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold mb-4">⚠️ Red Flags</h2>
                <div className="space-y-4">
                  {result.red_flags.map((flag, index) => (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border ${getSeverityColor(flag.severity)}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-bold text-lg">{flag.title}</h3>
                        <span className="text-xs uppercase font-semibold px-2 py-1 rounded">
                          {flag.severity}
                        </span>
                      </div>
                      <p className="text-sm mb-2">{flag.explanation}</p>
                      <div className="mt-3 pt-3 border-t border-current border-opacity-20">
                        <p className="text-sm font-semibold mb-1">💡 Negotiation Tip:</p>
                        <p className="text-sm">{flag.negotiation_tip}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Draft Email */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold mb-4">📧 Draft Response Email</h2>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap font-mono text-gray-700 border border-gray-200">
                {result.draft_email}
              </pre>
              <button
                onClick={() => navigator.clipboard.writeText(result.draft_email)}
                className="mt-4 bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
