#!/usr/bin/env python3
"""
Generates the main dashboard (index.html) from openrouter_data.json.
"""
import json
import pathlib
from jinja2 import Environment, FileSystemLoader, select_autoescape


def _round_to_1024(value: int) -> int:
    return int(round(value / 1024.0) * 1024)


def _format_context_label(value: int) -> str:
    if value >= 1024 * 1024:
        m = value / (1024 * 1024)
        label = f"{int(m)}M+" if m.is_integer() else f"{m:.1f}M+"
        return label
    k = int(round(value / 1024.0))
    return f"{k}k+"


def _percentile(sorted_vals, pct: int) -> int:
    if not sorted_vals:
        return 0
    n = len(sorted_vals)
    idx = int(round((pct / 100) * (n - 1)))
    return sorted_vals[max(0, min(idx, n - 1))]


def compute_context_options(models) -> list[dict]:
    contexts = []
    for m in models:
        ctx = m.get("context_length")
        if ctx:
            contexts.append(int(ctx))

    if not contexts:
        return [{"value": 0, "label": "Any"}]

    contexts.sort()
    unique = sorted(set(contexts))
    if len(unique) <= 10:
        values = unique
    else:
        candidates = [
            _percentile(contexts, 10),
            _percentile(contexts, 25),
            _percentile(contexts, 50),
            _percentile(contexts, 75),
            _percentile(contexts, 90),
            _percentile(contexts, 95),
            contexts[-1],
        ]
        values = sorted(set(_round_to_1024(v) for v in candidates if v > 0))

    options = [{"value": 0, "label": "Any"}]
    options.extend({"value": v, "label": _format_context_label(v)} for v in values)
    return options

def compute_provider_options(data) -> list[str]:
    providers = set()
    for cat in data.values():
        for m in cat:
            model_id = m.get("id", "")
            if "/" in model_id:
                provider = model_id.split("/")[0]
                providers.add(provider)
    
    # Sort by number of models per provider to show most important ones first
    provider_counts = {}
    for cat in data.values():
        for m in cat:
            model_id = m.get("id", "")
            if "/" in model_id:
                provider = model_id.split("/")[0]
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
    
    sorted_providers = sorted(providers, key=lambda p: provider_counts.get(p, 0), reverse=True)
    return sorted_providers

def generate_dashboard():
    # Paths
    # scripts/build.py
    base_dir = pathlib.Path(__file__).resolve().parent
    root_dir = base_dir.parent
    
    templates_dir = base_dir / "templates"
    # UPDATED: File name
    data_file = root_dir / "data" / "openrouter_data.json"
    output_file = root_dir / "docs" / "index.html"
    
    # Check data
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return

    # Load Data
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"📊 Loaded data for dashboard generation")

    # Setup Jinja2
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Render
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    template = env.get_template('dashboard.html')
    context_options = compute_context_options(data.get("text", []))
    provider_options = compute_provider_options(data)
    
    html_content = template.render(
        models_json=json.dumps(data, indent=2),
        generated_at=now,
        context_options=context_options,
        provider_options=provider_options,
    )
    
    import shutil
    
    # Save index.html
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    # Copy static assets
    static_src = base_dir / "static"
    if static_src.exists():
        for item in static_src.iterdir():
            if item.is_file():
                shutil.copy2(item, output_file.parent / item.name)
        print(f"📦 Copied static assets to {output_file.parent}")
        
    print(f"✅ Generated Dashboard at {output_file}")

if __name__ == "__main__":
    generate_dashboard()
