type Props = {
  answer: string;
  steps: string[];
};

export default function AnswerPanel({ answer, steps }: Props) {
  return (
    <div className="mt-4 rounded border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-800">Answer</h3>
      <p className="mt-2 text-slate-700">{answer}</p>
      <h4 className="mt-4 text-sm font-semibold text-slate-700">Explanation (steps)</h4>
      <ul className="list-disc list-inside text-sm text-slate-600 mt-2 space-y-1">
        {steps.map((step, idx) => (
          <li key={idx}>{step}</li>
        ))}
      </ul>
    </div>
  );
}
