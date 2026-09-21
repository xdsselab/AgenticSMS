"""Generate intermediate data files from the raw CSV — run once, then edit figures freely."""
import csv, os, json
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "all_summary_final_665.csv")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---- Constants ----
RQ1_KEYS = [
    "RQ1_Perception_ContextAcquisition", "RQ1_Environment_Interaction",
    "RQ1_Tool_CapabilityUse", "RQ1_Memory_StateManagement",
    "RQ1_Reasoning_Planning", "RQ1_Action_Execution",
    "RQ1_Feedback_Reflection", "RQ1_Human_Collaboration",
    "RQ1_Role_MultiagentCoordination", "RQ1_Governance_Traceability",
]

# ---- Helpers ----
def parse_multi(val):
    if not val or val.strip() == "":
        return []
    return [v.strip() for v in val.replace("; ", ";").split(";") if v.strip()]

def save_csv(data, fname):
    path = os.path.join(DATA_DIR, fname)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        if not data:
            return
        if isinstance(data, list) and isinstance(data[0], dict):
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)
        elif isinstance(data, list):
            w = csv.writer(f)
            w.writerows(data)
        else:
            w = csv.writer(f)
            for k, v in data.items():
                w.writerow([k, v])

# ---- Load raw data ----
with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader if r.get("title", "").strip()]
N = len(rows)
assert N == 665 and len({r["key"] for r in rows}) == N
for r in rows:
    r["RQ3_application_domain"] = r.get("RQ3_application_domain", "").strip().lower()
print(f"Loaded {N} papers")

# ============================================================
# 1. RQ1 Feature Frequencies
# ============================================================
rq1_counts = Counter()
for r in rows:
    for k in RQ1_KEYS:
        if r.get(k, "no").lower() == "yes":
            rq1_counts[k] += 1
save_csv([{"feature": k, "count": rq1_counts.get(k, 0), "pct": round(rq1_counts.get(k, 0) / N * 100, 1)} for k in RQ1_KEYS], "rq1_frequencies.csv")
print(f"  [1/16] rq1_frequencies.csv")

# ============================================================
# 2. RQ1 Co-occurrence Matrix
# ============================================================
import numpy as np
cooc = np.zeros((10, 10), dtype=int)
for r in rows:
    flags = [1 if r.get(k, "no").lower() == "yes" else 0 for k in RQ1_KEYS]
    for i in range(10):
        for j in range(10):
            if flags[i] and flags[j]:
                cooc[i][j] += 1
cooc_data = []
for i in range(10):
    for j in range(10):
        union = int(cooc[i][i] + cooc[j][j] - cooc[i][j])
        cooc_data.append({"feature_i": RQ1_KEYS[i], "feature_j": RQ1_KEYS[j], "count": int(cooc[i][j]), "jaccard": int(cooc[i][j]) / union if union else 0.0})
save_csv(cooc_data, "rq1_cooccurrence.csv")
print(f"  [2/16] rq1_cooccurrence.csv")

# ============================================================
# 3. RQ1 Feature Count Distribution
# ============================================================
feat_counts = Counter()
for r in rows:
    nf = sum(1 for k in RQ1_KEYS if r.get(k, "no").lower() == "yes")
    feat_counts[nf] += 1
save_csv([{"num_features": k, "count": v} for k, v in sorted(feat_counts.items())], "rq1_feature_count.csv")
print(f"  [3/16] rq1_feature_count.csv")

# ============================================================
# 4. RQ2 System Form Distribution
# ============================================================
rq2_primary = Counter(r.get("RQ2_primary_form", "?").strip() for r in rows if r.get("RQ2_primary_form", "").strip())
rq2_secondary = Counter()
for r in rows:
    v = r.get("RQ2_secondary_form", "").strip()
    if v:
        rq2_secondary[v] += 1
# Exclude the three Hybrid/Other papers from this chart only.
all_forms = sorted(set(list(rq2_primary.keys()) + list(rq2_secondary.keys())))
all_forms = [f for f in all_forms if f != "Hybrid_Other"]
save_csv([{"form": k, "primary_count": rq2_primary.get(k, 0), "secondary_count": rq2_secondary.get(k, 0)} for k in all_forms], "rq2_distribution.csv")
print(f"  [4/16] rq2_distribution.csv")

# ============================================================
# 5. RQ2 System Form x Application Domain
# ============================================================
form_domain = defaultdict(lambda: defaultdict(int))
for r in rows:
    f = r.get("RQ2_primary_form", "?").strip()
    d = r.get("RQ3_application_domain", "?").strip()
    form_domain[f][d] += 1
fd_data = []
for f in form_domain:
    if f == "Hybrid_Other":
        continue
    for d in form_domain[f]:
        if d == "other":
            continue
        fd_data.append({"form": f, "domain": d, "count": form_domain[f][d]})
save_csv(fd_data, "rq2_domain_cross.csv")
print(f"  [5/16] rq2_domain_cross.csv")

# ============================================================
# 6. RQ3 Application Domains
# ============================================================
rq3_domains = Counter(r.get("RQ3_application_domain", "?").strip() for r in rows if r.get("RQ3_application_domain", "").strip())
# Exclude "other" from the bar chart (handled by Table tab:other_sub)
rq3_domains_filtered = [(k, v) for k, v in rq3_domains.most_common() if k != "other"]
save_csv([{"domain": k, "count": v, "pct": round(v / N * 100, 1)} for k, v in rq3_domains_filtered], "rq3_domains.csv")
print(f"  [6/16] rq3_domains.csv")

# ============================================================
# 7. RQ3 Domain x Feature Prevalence (raw counts)
# ============================================================
top_d_all = [d for d, _ in rq3_domains.most_common(13) if d != "other"][:12]
df_data = []
for d in top_d_all:
    for fk in RQ1_KEYS:
        cnt = sum(1 for r in rows if r.get("RQ3_application_domain", "").strip() == d and r.get(fk, "no").lower() == "yes")
        df_data.append({"domain": d, "feature": fk.replace("RQ1_", ""), "count": cnt})
save_csv(df_data, "rq3_domain_features.csv")
print(f"  [7/16] rq3_domain_features.csv")

# ============================================================
# 8. RQ4 Evaluation Types
# ============================================================
# Clean and normalize evaluation types into 8 canonical categories
CANONICAL_EVAL_TYPES = {
    "benchmark": ["benchmark"],
    "ablation": ["ablation"],
    "experiment": [
        "experiment", "comparison", "comparative", "simulation",
        "testing", "demonstration", "reproduction",
        "statistical_analysis", "sensitivity_analysis",
        "robustness", "error_analysis", "qualitative_analysis",
        "offline_experiment",
    ],
    "case_study": ["case_study", "case study"],
    "human_evaluation": ["human_evaluation", "clinical_efficacy"],
    "real_world_deployment": ["real_world_deployment"],
    "user_study": [
        "user_study", "user_analysis", "formative_study",
        "post-study", "questionnaire",
    ],
    "expert_evaluation": ["expert_evaluation"],
}

def classify_eval_type(raw):
    t = raw.strip().lower().replace(" ", "_").replace("-", "_")
    for canonical, patterns in CANONICAL_EVAL_TYPES.items():
        for p in patterns:
            if p.replace(" ", "_").replace("-", "_") in t:
                return canonical
    return None  # excluded

eval_types = Counter()
excluded_eval = 0
for r in rows:
    categories = set()
    for t in parse_multi(r.get("RQ4_evaluation_type", "")):
        cat = classify_eval_type(t)
        if cat:
            categories.add(cat)
        else:
            excluded_eval += 1
    r["_evaluation_categories"] = categories
    eval_types.update(categories)
save_csv([{"type": k, "count": v, "pct": round(v / N * 100, 1)} for k, v in eval_types.most_common()], "rq4_evaluation.csv")
print(f"  [8/16] rq4_evaluation.csv (8 categories, {excluded_eval} excluded)")

# ============================================================
# 9. RQ4 Reproducibility
# ============================================================
repro = Counter(r.get("RQ4_reproducibility", "?").strip() for r in rows)
save_csv([{"status": k, "count": v} for k, v in repro.most_common()], "rq4_reproducibility.csv")
print(f"  [9/16] rq4_reproducibility.csv")

# ============================================================
# 10. Year Trends
# ============================================================
years = Counter(r.get("year", "?").strip() for r in rows)
save_csv([{"year": k, "count": v} for k, v in sorted(years.items()) if k.isdigit()], "year_trends.csv")
print(f" [10/16] year_trends.csv")

# ============================================================
# 11. Publication Types
# ============================================================
pub_types = Counter(r.get("publication_type", "?").strip() for r in rows)
save_csv([{"type": k, "count": v, "pct": round(v / N * 100, 1)} for k, v in pub_types.most_common()], "publication_stats.csv")
print(f" [11/16] publication_stats.csv")

# ============================================================
# 12. Architecture — Diagram Types
# ============================================================
# Clean and normalize diagram types into 5 canonical categories
CANONICAL_DIAGRAM_TYPES = {
    "system architecture": [
        "system architecture", "architecture", "system_architecture",
        "chatbot architecture", "infrastructure",
    ],
    "workflow / flowchart": [
        "workflow", "flowchart", "flow",
    ],
    "agent interaction": [
        "agent interaction", "interaction",
    ],
    "component diagram": [
        "component",
    ],
    "sequence diagram": [
        "sequence",
    ],
}

def classify_diagram_type(raw):
    t = raw.strip().lower()
    # Remove parenthetical figure references
    import re
    t = re.sub(r'\s*\(.*?\)', '', t)
    t = re.sub(r'\s*/\s*', ' ', t)
    t = t.strip()
    for canonical, patterns in CANONICAL_DIAGRAM_TYPES.items():
        for p in patterns:
            if p in t:
                return canonical
    return None  # excluded

diag_types = Counter()
excluded_count = 0
for r in rows:
    categories = set()
    for t in parse_multi(r.get("Arch_diagram_types", "")):
        cat = classify_diagram_type(t)
        if cat:
            categories.add(cat)
        else:
            excluded_count += 1
    diag_types.update(categories)
save_csv([{"type": k, "count": v} for k, v in diag_types.most_common()], "diagram_types.csv")
print(f"  [12a] diagram_types.csv (5 categories, {excluded_count} excluded)")


# ============================================================
# 13. Architecture — System Evolution
# ============================================================
evol = Counter(r.get("Arch_system_evolution", "?").strip().lower() for r in rows)
save_csv([{"status": k, "count": v} for k, v in evol.most_common()], "system_evolution.csv")
print(f" [13/16] system_evolution.csv")

# ============================================================
# 14. Cross: Human-Collaboration x Evaluation Methods
# ============================================================
has_human = [r for r in rows if r.get("RQ1_Human_Collaboration", "no").lower() == "yes"]
no_human = [r for r in rows if r.get("RQ1_Human_Collaboration", "no").lower() != "yes"]

def eval_pct(group, eval_type):
    if not group:
        return 0.0
    return sum(1 for r in group if eval_type in r["_evaluation_categories"]) / len(group) * 100

save_csv([
    {"group": "with_human_collab", "n": len(has_human),
     "user_study_pct": round(eval_pct(has_human, "user_study"), 1),
     "human_evaluation_pct": round(eval_pct(has_human, "human_evaluation"), 1)},
    {"group": "without_human_collab", "n": len(no_human),
     "user_study_pct": round(eval_pct(no_human, "user_study"), 1),
     "human_evaluation_pct": round(eval_pct(no_human, "human_evaluation"), 1)},
], "rq1_human_eval_cross.csv")
print(f" [14/16] rq1_human_eval_cross.csv")

# ============================================================
# 15. Cross: System Forms x Evaluation Methods
# ============================================================
top_forms = ["ToolAugmented_DomainSystem", "MultiAgent_CollaborationSystem",
             "SoftwareEngineering_AgenticSystem", "DigitalEnvironment_OperationSystem",
             "ResearchAutomation_System"]
top_evals = ["benchmark", "ablation", "experiment", "case_study",
             "real_world_deployment", "user_study"]

forms_eval_data = []
for form in top_forms:
    form_rows = [r for r in rows if r.get("RQ2_primary_form", "").strip() == form]
    n_form = len(form_rows)
    for ev in top_evals:
        cnt = sum(1 for r in form_rows if ev in r["_evaluation_categories"])
        pct = round(cnt / n_form * 100, 1) if n_form else 0
        forms_eval_data.append({"form": form, "eval_type": ev, "count": cnt, "pct": pct})
save_csv(forms_eval_data, "rq2_forms_eval_cross.csv")
print(f" [15/16] rq2_forms_eval_cross.csv")

# ============================================================
# 16. Source Database Breakdown
# ============================================================
src_counts = Counter(r.get("source_db", "?") for r in rows)
save_csv([{"source": k, "count": v} for k, v in src_counts.most_common()], "source_breakdown.csv")
print(f" [16/16] source_breakdown.csv")

# Derived descriptive checks use the same per-paper categories as every figure.
analysis_checks = {
    "evaluation_method_counts": dict(sorted(Counter(len(r["_evaluation_categories"]) for r in rows).items())),
    "statistical_analysis_count": sum(r.get("RQ4_statistical_analysis", "").lower().startswith("yes") for r in rows),
    "governance_mean_jaccard": float(np.mean([d["jaccard"] for d in cooc_data if d["feature_i"] == "RQ1_Governance_Traceability" and d["feature_j"] != d["feature_i"]])),
}
with open(os.path.join(DATA_DIR, "analysis_checks.json"), "w", encoding="utf-8") as f:
    json.dump(analysis_checks, f, indent=2)

# ============================================================
# Metadata
# ============================================================
with open(os.path.join(DATA_DIR, "metadata.json"), "w", encoding="utf-8") as f:
    json.dump({"N": N, "description": "Intermediate data for SMS figures"}, f, ensure_ascii=False, indent=2)

print(f"\nDone! {N} papers. All data saved to {DATA_DIR}/")
print(f"Next: run draw_all.py to generate figures.")
