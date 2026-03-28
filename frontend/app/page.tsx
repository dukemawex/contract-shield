'use client';

import { useState } from 'react';

interface RedFlag {
  title: string;
  severity: 'low' | 'medium' | 'high';
  explanation: string;
  negotiation_tip: string;
}

interface AnalysisResult {
  risk_score: number;
  severity: string;
  red_flags: RedFlag[];
  negotiation_tips: string[];
  draft_email: string;
  summary: string;
}

interface UserStatus {
  email: string;
  is_pro: boolean;
  analyses_used: number;
  analyses_remaining: number | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  // Email gate state
  const [email, setEmail] = useState('');
  const [emailInput, setEmailInput] = useState('');
  const [userStatus, setUserStatus] = useState<UserStatus | null>(null);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);

  // Analysis state
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  // Paywall modal state
  const [showPaywall, setShowPaywall] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailInput.trim()) return;

    setEmailLoading(true);
    setEmailError(null);

    try {
      const res = await fetch(`${API_URL}/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailInput.trim() }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to register email');
      }

      const status: UserStatus = await res.json();
      setEmail(status.email);
      setUserStatus(status);
    } catch (err) {
      setEmailError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setEmailLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setAnalyzeError(null);
      setResult(null);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !email) return;

    setLoading(true);
    setAnalyzeError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('email', email);

    try {
      const res = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (res.status === 403) {
        setShowPaywall(true);
        setLoading(false);
        return;
      }

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Analysis failed');
      }

      const data: AnalysisResult = await res.json();
      setResult(data);

      // Refresh status
      const statusRes = await fetch(`${API_URL}/users/status?email=${encodeURIComponent(email)}`);
      if (statusRes.ok) {
        setUserStatus(await statusRes.json());
      }
    } catch (err) {
      setAnalyzeError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async () => {
    if (!email) return;
    setCheckoutLoading(true);

    try {
      const res = await fetch(`${API_URL}/billing/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) throw new Error('Could not create checkout');

      const { checkout_url } = await res.json();
      window.location.href = checkout_url;
    } catch {
      setCheckoutLoading(false);
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
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">🛡️ Contract Shield</h1>
          <p className="text-gray-600">AI-powered contract risk analysis for freelancers</p>
        </div>

        {/* Step 1: Email Gate */}
        {!email && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-700 mb-1">Get your free analysis</h2>
            <p className="text-sm text-gray-500 mb-4">
              Enter your email to unlock 3 free contract analyses.
            </p>
            <form onSubmit={handleEmailSubmit} className="space-y-3">
              <input
                type="email"
                required
                placeholder="you@example.com"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <button
                type="submit"
                disabled={emailLoading}
                className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {emailLoading ? 'Saving…' : 'Get Free Access →'}
              </button>
            </form>
            {emailError && (
              <p className="mt-3 text-sm text-red-600">{emailError}</p>
            )}
          </div>
        )}

        {/* Step 2: Upload + Status bar */}
        {email && userStatus && (
          <>
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-gray-600">
                  Signed in as <strong>{email}</strong>
                </span>
                {userStatus.is_pro ? (
                  <span className="bg-indigo-100 text-indigo-700 text-xs font-semibold px-3 py-1 rounded-full">
                    ✨ Pro — Unlimited
                  </span>
                ) : (
                  <span className="text-sm text-gray-500">
                    {userStatus.analyses_remaining} free{' '}
                    {userStatus.analyses_remaining === 1 ? 'analysis' : 'analyses'} left
                  </span>
                )}
              </div>

              <form onSubmit={handleAnalyze} className="space-y-4">
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
                  {loading ? 'Analyzing…' : 'Analyze Contract'}
                </button>
              </form>

              {analyzeError && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {analyzeError}
                </div>
              )}
            </div>

            {/* Not-pro upgrade nudge */}
            {!userStatus.is_pro && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-6 flex items-center justify-between">
                <p className="text-sm text-indigo-700">
                  Upgrade to <strong>Pro</strong> for unlimited analyses — $9/mo
                </p>
                <button
                  onClick={handleUpgrade}
                  disabled={checkoutLoading}
                  className="bg-indigo-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors ml-4 whitespace-nowrap"
                >
                  {checkoutLoading ? 'Loading…' : 'Upgrade to Pro'}
                </button>
              </div>
            )}
          </>
        )}

        {/* Results */}
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

            {/* Summary */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold mb-4">Contract Summary</h2>
              <p className="text-gray-700 leading-relaxed">{result.summary}</p>
            </div>

            {/* Red Flags */}
            {result.red_flags.length > 0 && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold mb-4">⚠️ Red Flags</h2>
                <div className="space-y-4">
                  {result.red_flags.map((flag) => (
                    <div key={`${flag.title}-${flag.severity}`} className={`p-4 rounded-lg border ${getSeverityColor(flag.severity)}`}>
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

      {/* Paywall Modal */}
      {showPaywall && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center">
            <div className="text-5xl mb-4">🛡️</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">You&apos;ve used your 3 free analyses</h2>
            <p className="text-gray-500 mb-6">
              Upgrade to <strong>Contract Shield Pro</strong> for unlimited analyses and protect
              every contract you sign.
            </p>
            <div className="bg-indigo-50 rounded-xl p-4 mb-6">
              <p className="text-3xl font-bold text-indigo-600">$9<span className="text-base font-normal text-gray-500">/month</span></p>
              <ul className="text-sm text-gray-600 mt-2 space-y-1">
                <li>✅ Unlimited contract analyses</li>
                <li>✅ AI-powered risk detection</li>
                <li>✅ Negotiation tips &amp; draft emails</li>
                <li>✅ Cancel anytime</li>
              </ul>
            </div>
            <button
              onClick={handleUpgrade}
              disabled={checkoutLoading}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg font-bold text-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {checkoutLoading ? 'Loading…' : 'Upgrade to Pro — $9/mo'}
            </button>
            <button
              onClick={() => setShowPaywall(false)}
              className="mt-3 text-sm text-gray-400 hover:text-gray-600 underline"
            >
              Maybe later
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
