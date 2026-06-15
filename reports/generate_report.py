from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MART_PATH = PROJECT_ROOT / "datasets" / "marts" / "narrativeiq_mart.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "generated" / "narrativeiq_exhibition_report.html"


def text(value: Any) -> str:
    return escape(str(value))


def compact(value: int | float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def score(value: int | float) -> str:
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


def pct(value: int | float) -> str:
    return f"{float(value):.1f}%"


def bar(value: int | float, color: str = "#15d8ff") -> str:
    width = max(0, min(100, float(value)))
    return (
        '<div class="bar-track">'
        f'<span class="bar-fill" style="width:{width:.2f}%;background:{color}"></span>'
        "</div>"
    )


def stat_card(label: str, value: str, note: str = "") -> str:
    return (
        '<article class="stat-card">'
        f"<span>{text(label)}</span>"
        f"<strong>{text(value)}</strong>"
        f"<small>{text(note)}</small>"
        "</article>"
    )


def table(headers: list[str], rows: list[list[Any]]) -> str:
    head = "".join(f"<th>{text(header)}</th>" for header in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{text(cell)}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def render_report(mart: dict[str, Any]) -> str:
    overview = mart["overview"]
    report = mart["reportSummary"]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    top_event = mart["events"][0]
    top_narrative = mart["narratives"][0]

    sentiment_rows = [
        [item["label"], compact(item["value"]), pct(item["value"] / max(1, sum(x["value"] for x in overview["sentimentDistribution"])) * 100)]
        for item in overview["sentimentDistribution"]
    ]

    event_rows = [
        [
            item["name"],
            item["category"],
            item["region"],
            item["lifecycleStage"],
            score(item["narrativeStrength"]),
            score(item["influenceScore"]),
            item["sentimentLabel"],
        ]
        for item in mart["events"]
    ]

    narrative_rows = [
        [
            item["topic"],
            item["eventName"],
            item["lifecycleStage"],
            score(item["latestStrength"]),
            pct(item["growthRate"]),
            score(item["influenceScore"]),
        ]
        for item in mart["narratives"][:8]
    ]

    entity_rows = [
        [
            item["name"],
            item["type"],
            item["eventName"],
            compact(item["latestMentions"]),
            score(item["mentionStrength"]),
        ]
        for item in mart["entities"][:10]
    ]

    quality_cards = "\n".join(
        (
            '<article class="quality-card">'
            f"<div><strong>{text(row['dataset'])}</strong><span>{compact(row['record_count'])} records</span></div>"
            f"{bar(row['quality_score'], '#3ddc97')}"
            f"<small>{score(row['quality_score'])}% quality</small>"
            "</article>"
        )
        for row in mart["dataQuality"][:8]
    )

    forecast_rows = [
        [point["period"], score(point["strength"]), score(point["confidence"])]
        for point in mart["predictions"][0]["forecast"]
    ]

    growing_topic_cards = "\n".join(
        (
            '<article class="topic-card">'
            f"<span>{text(item['eventName'])}</span>"
            f"<strong>{text(item['topic'])}</strong>"
            f"{bar(item['growthRate'], '#f6c85f')}"
            f"<small>Growth {pct(item['growthRate'])} / momentum {score(item['momentum'])}</small>"
            "</article>"
        )
        for item in mart["topGrowingTopics"][:8]
    )

    insight_cards = "\n".join(
        (
            '<article class="insight-card">'
            f"<span>{text(item['severity'])}</span>"
            f"<strong>{text(item['title'])}</strong>"
            f"<p>{text(item['body'])}</p>"
            "</article>"
        )
        for item in mart["intelligenceFeed"][:4]
    )

    demo_steps = "".join(f"<li>{text(step)}</li>" for step in report["recommendedDemoFlow"])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>NarrativeIQ Exhibition Intelligence Report</title>
  <style>
    :root {{
      --bg: #050914;
      --panel: #0d1324;
      --panel-strong: #111a2f;
      --line: #26324a;
      --text: #f8fbff;
      --muted: #9ca8ba;
      --cyan: #15d8ff;
      --signal: #f6c85f;
      --mint: #3ddc97;
      --coral: #ff6b6b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--text);
      background: var(--bg);
      font-family: Inter, Segoe UI, Arial, sans-serif;
      letter-spacing: 0;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    .hero, section {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(13, 19, 36, 0.94);
      box-shadow: 0 18px 70px rgba(0, 0, 0, 0.25);
    }}
    .hero {{
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      gap: 24px;
      align-items: center;
      padding: 28px;
      margin-bottom: 18px;
    }}
    .hero img {{ width: 100%; height: auto; object-fit: contain; background: #09111f; border: 1px solid #1b2740; border-radius: 8px; padding: 16px; }}
    .eyebrow {{ margin: 0 0 8px; color: var(--cyan); font-size: 12px; font-weight: 800; text-transform: uppercase; }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 12px; font-size: 38px; line-height: 1.08; }}
    h2 {{ margin-bottom: 14px; font-size: 23px; }}
    p {{ color: var(--muted); line-height: 1.6; }}
    section {{ padding: 22px; margin-bottom: 18px; }}
    .stat-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }}
    .stat-card, .topic-card, .quality-card, .insight-card {{
      display: grid;
      gap: 8px;
      padding: 14px;
      background: #09111f;
      border: 1px solid #1b2740;
      border-radius: 8px;
    }}
    .stat-card span, .topic-card span, .insight-card span {{ color: var(--cyan); font-size: 11px; font-weight: 800; text-transform: uppercase; }}
    .stat-card strong {{ font-size: 26px; }}
    small {{ color: var(--muted); }}
    .split {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 18px; }}
    .topic-grid, .quality-grid, .insight-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .topic-card strong, .insight-card strong {{ font-size: 18px; }}
    .bar-track {{ height: 8px; overflow: hidden; background: #111a2f; border-radius: 999px; }}
    .bar-fill {{ display: block; height: 100%; border-radius: 999px; }}
    table {{ width: 100%; border-collapse: collapse; overflow: hidden; border-radius: 8px; }}
    th, td {{ padding: 10px 11px; border-bottom: 1px solid #1b2740; text-align: left; vertical-align: top; }}
    th {{ color: var(--cyan); background: #09111f; font-size: 12px; text-transform: uppercase; }}
    td {{ color: #dce6f6; font-size: 13px; }}
    ol {{ margin-bottom: 0; color: #dce6f6; line-height: 1.7; }}
    .footer {{ color: var(--muted); text-align: center; font-size: 12px; }}
    @media (max-width: 840px) {{
      main {{ padding: 14px; }}
      .hero, .split, .stat-grid, .topic-grid, .quality-grid, .insight-grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 30px; }}
    }}
    @media print {{
      body {{ background: white; color: #101827; }}
      main {{ max-width: none; padding: 0; }}
      .hero, section {{ box-shadow: none; break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <img src="../assets/narrativeiq-full.png" alt="NarrativeIQ full logo" />
      <div>
        <p class="eyebrow">Data Warehousing and Big Data Lab Exhibition Report</p>
        <h1>{text(report["title"])}</h1>
        <p>{text(report["primaryFinding"])}</p>
        <p><strong>Generated:</strong> {text(generated_at)} &nbsp; <strong>Historical through:</strong> {text(mart["historicalThrough"])}</p>
      </div>
    </header>

    <section>
      <h2>Executive Warehouse Snapshot</h2>
      <div class="stat-grid">
        {stat_card("Raw Records", compact(overview["totalRecords"]), "Generated content facts")}
        {stat_card("Active Events", str(overview["activeEvents"]), "Event dimension")}
        {stat_card("Narratives", str(overview["activeNarratives"]), "Narrative fact groups")}
        {stat_card("Health Score", score(overview["narrativeHealthScore"]), "Cross-event signal")}
        {stat_card("Quality", score(overview["warehouseQualityScore"]) + "%", "ETL profile")}
      </div>
    </section>

    <section class="split">
      <div>
        <h2>Primary Finding</h2>
        <p>{text(report["primaryFinding"])}</p>
        <p>The strongest current event is <strong>{text(top_event["name"])}</strong>, while the leading narrative is <strong>{text(top_narrative["topic"])}</strong>.</p>
      </div>
      <div>
        <h2>Recommended Demo Flow</h2>
        <ol>{demo_steps}</ol>
      </div>
    </section>

    <section>
      <h2>Event Monitor</h2>
      {table(["Event", "Category", "Region", "Stage", "Strength", "Influence", "Sentiment"], event_rows)}
    </section>

    <section>
      <h2>Narrative Lifecycle Ranking</h2>
      {table(["Narrative", "Event", "Stage", "Strength", "Growth", "Influence"], narrative_rows)}
    </section>

    <section>
      <h2>Top Growing Topics</h2>
      <div class="topic-grid">{growing_topic_cards}</div>
    </section>

    <section class="split">
      <div>
        <h2>Entity Intelligence</h2>
        {table(["Entity", "Type", "Event", "Latest Mentions", "Strength"], entity_rows)}
      </div>
      <div>
        <h2>Sentiment Mix</h2>
        {table(["Label", "Signals", "Share"], sentiment_rows)}
        <h2 style="margin-top:22px;">Forecast Preview</h2>
        {table(["Period", "Strength", "Confidence"], forecast_rows)}
      </div>
    </section>

    <section>
      <h2>AI-Ready Insight Cards</h2>
      <div class="insight-grid">{insight_cards}</div>
    </section>

    <section>
      <h2>ETL Quality Profile</h2>
      <div class="quality-grid">{quality_cards}</div>
    </section>

    <p class="footer">NarrativeIQ - warehouse-backed narrative intelligence report generated from datasets/marts/narrativeiq_mart.json.</p>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the NarrativeIQ exhibition HTML report.")
    parser.add_argument("--mart", type=Path, default=DEFAULT_MART_PATH, help="Path to narrativeiq_mart.json.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output HTML path.")
    args = parser.parse_args()

    with args.mart.open("r", encoding="utf-8") as handle:
        mart = json.load(handle)

    html = render_report(mart)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")

    print(
        {
            "status": "generated",
            "output": str(args.output),
            "records": mart["overview"]["totalRecords"],
            "historicalThrough": mart["historicalThrough"],
        }
    )


if __name__ == "__main__":
    main()
