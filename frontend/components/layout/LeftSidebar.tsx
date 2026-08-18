export default function LeftSidebar() {
  const items = [
    { title: "Real student reviews", desc: "from Reddit (live)" },
    { title: "Compare universities", desc: "side-by-side" },
    { title: "Make better, informed", desc: "decisions" },
    { title: "100% Free to use", desc: "No sign-up required" },
  ];

  return (
    <div className="panel">
      <div className="section-title dark">Why use this?</div>
      {items.map((item) => (
        <div className="why-item" key={item.title}>
          <div className="why-check">✓</div>
          <div>
            <div className="why-item-title">{item.title}</div>
            <div className="why-item-desc">{item.desc}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
