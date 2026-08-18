export default function AboutPage() {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-extrabold text-gray-900 mb-4">About Us</h2>
      <p className="text-sm text-gray-600 leading-relaxed mb-4">
        <strong>University Comparison Bot</strong> helps students research and compare universities
        using real, live student discussions pulled from Reddit, analysed by AI to surface
        academics, student life, value, and career outcomes side-by-side.
      </p>
      <ul className="space-y-2 text-sm text-gray-600 list-disc list-inside">
        <li>Built to make university research faster and less overwhelming.</li>
        <li>Combines live Reddit sentiment with an AI summary — not an official ranking.</li>
        <li>100% free, no sign-up required.</li>
      </ul>
    </div>
  );
}
