interface RightSidebarProps {
  popularComparisons: string[];
}

export default function RightSidebar({ popularComparisons }: RightSidebarProps) {
  const features = [
    { title: "Real student opinions", desc: "from Reddit communities" },
    { title: "Side-by-side comparison", desc: "of key aspects" },
    { title: "Pros & Cons analysis", desc: "for each university" },
    { title: "AI-powered summary", desc: "with key takeaways" },
  ];

  return (
    <>
      <div className="panel" style={{ marginBottom: "var(--space-5)" }}>
        <div className="section-title dark">What you&apos;ll get</div>
        {features.map((f) => (
          <div className="feat-item" key={f.title}>
            <div>
              <div className="feat-item-title">{f.title}</div>
              <div className="feat-item-desc">{f.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="panel">
        <div className="section-title">Popular Pakistani Uni Comparisons</div>
        {popularComparisons.map((comp, i) => (
          <div className="pop-row" key={comp}>
            <span>
              <span className="pop-rank">#{i + 1}</span>
              <span className="pop-name">{comp}</span>
            </span>
            <span className="pop-chev">›</span>
          </div>
        ))}
        <div className="tip-box">
          <div className="tip-box-title">Tip</div>
          <div className="tip-box-desc">Be specific with university names for more accurate results.</div>
        </div>
      </div>
    </>
  );
}
