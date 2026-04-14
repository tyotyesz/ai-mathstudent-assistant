"use client";

type Props = {
  message: string;
  onRetry: () => void;
};

export default function ErrorPanel({ message, onRetry }: Props) {
  return (
    <div className="mt-4 border border-rose-200 bg-rose-50 text-rose-700 rounded p-4">
      <p className="font-semibold">Service unavailable</p>
      <p className="text-sm mt-1">{message}</p>
      <button
        onClick={onRetry}
        className="mt-3 inline-flex items-center px-3 py-2 rounded bg-rose-600 text-white text-sm font-semibold hover:bg-rose-700"
      >
        Retry
      </button>
    </div>
  );
}
