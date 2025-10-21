"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

export default function CallbackPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [authCode, setAuthCode] = useState('');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const s = searchParams.get('s');
        const code = searchParams.get('code');
        const auth_code = searchParams.get('auth_code');
        const state = searchParams.get('state');

        // Forward the callback to the backend
        const response = await fetch(`https://optionstrategy-rj2e.onrender.com/callback?s=${s}&code=${code}&auth_code=${auth_code}&state=${state}`);
        const data = await response.json();

        if (data.success) {
          setStatus('success');
          setMessage(data.message);
          setAuthCode(data.auth_code);
        } else {
          setStatus('error');
          setMessage(data.message);
        }
      } catch (error) {
        setStatus('error');
        setMessage('Error processing callback');
      }
    };

    handleCallback();
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-6">
        <div className="text-center">
          <div className="mb-4">
            {status === 'loading' && (
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            )}
            {status === 'success' && (
              <div className="text-green-600 text-6xl">✅</div>
            )}
            {status === 'error' && (
              <div className="text-red-600 text-6xl">❌</div>
            )}
          </div>

          <h1 className="text-2xl font-bold mb-4">
            {status === 'loading' && 'Processing Authentication...'}
            {status === 'success' && 'FYERS Authentication Successful!'}
            {status === 'error' && 'Authentication Failed'}
          </h1>

          <div className="text-left space-y-4">
            <p className="text-gray-700">{message}</p>

            {status === 'success' && authCode && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-800 mb-2">Your Access Token:</h3>
                <div className="bg-white border border-green-300 rounded p-3 mb-4">
                  <code className="text-sm break-all text-green-700">{authCode}</code>
                </div>
                
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-800 mb-2">Next Steps:</h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-blue-700">
                    <li>Copy the access token above</li>
                    <li>Go to your Render dashboard</li>
                    <li>Update the FYERS_ACCESS_TOKEN environment variable</li>
                    <li>Restart your application</li>
                    <li>Your scanner will now use live FYERS data!</li>
                  </ol>
                </div>
              </div>
            )}

            {status === 'error' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 className="font-semibold text-red-800 mb-2">What to do:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-red-700">
                  <li>Check your FYERS credentials</li>
                  <li>Make sure your app is properly configured</li>
                  <li>Try the authentication process again</li>
                </ul>
              </div>
            )}
          </div>

          <div className="mt-6">
            <a
              href="/"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              ← Back to Dashboard
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
