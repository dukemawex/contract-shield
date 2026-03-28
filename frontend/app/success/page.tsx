import Link from 'next/link';

export default function SuccessPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-10 text-center">
        <div className="text-6xl mb-4">🎉</div>
        <h1 className="text-3xl font-bold text-gray-800 mb-2">You&apos;re now on Pro!</h1>
        <p className="text-gray-500 mb-6">
          Welcome to <strong>Contract Shield Pro</strong>. You now have unlimited contract
          analyses. Start protecting your work today.
        </p>
        <Link
          href="/"
          className="inline-block bg-indigo-600 text-white py-3 px-8 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
        >
          Start Analyzing →
        </Link>
      </div>
    </div>
  );
}
