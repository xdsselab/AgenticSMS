"""Draw all figures from pre-computed data in figures/data/.

Usage:
    python draw_all.py              # draw all figures
    python draw_all.py --skip rq1   # skip RQ1 figures
    python draw_all.py --only rq4   # draw only RQ4 figures
"""
import csv, os, json, sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.container import BarContainer
import numpy as np

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(FIG_DIR, "data")

# ---- Font setup ----
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
                     "pdf.fonttype": 42, "ps.fonttype": 42})
plt.rcParams["axes.unicode_minus"] = False

# ---- Constants ----
RQ1_LABELS = [
    "Perception & Context\nAcquisition", "Environment\nInteraction",
    "Tool / Capability\nUse", "Memory / State\nManagement",
    "Reasoning &\nPlanning", "Action &\nExecution",
    "Feedback &\nReflection", "Human\nCollaboration",
    "Role / Multi-Agent\nCoordination", "Governance &\nTraceability",
]
RQ1_KEYS = [
    "RQ1_Perception_ContextAcquisition", "RQ1_Environment_Interaction",
    "RQ1_Tool_CapabilityUse", "RQ1_Memory_StateManagement",
    "RQ1_Reasoning_Planning", "RQ1_Action_Execution",
    "RQ1_Feedback_Reflection", "RQ1_Human_Collaboration",
    "RQ1_Role_MultiagentCoordination", "RQ1_Governance_Traceability",
]

# ---- Helpers ----
def read_csv(fname):
    path = os.path.join(DATA_DIR, fname)
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def fit_bar_labels(fig, padding_points=8):
    """Reserve measured space inside the axes without reducing label fonts.

    Run after tight_layout: long category names change the plotting width,
    so a fixed percentage added to xlim cannot reliably fit bar-end labels.
    Vertical bar labels receive the same protection at the top border.
    """
    for ax in fig.axes:
        bars = [c for c in ax.containers if isinstance(c, BarContainer)]
        labels = [t for t in ax.texts if t.get_visible() and t.get_text()]
        if not bars or not labels:
            continue
        horizontal = all(c.orientation == "horizontal" for c in bars)
        padding = padding_points * fig.dpi / 72
        for _ in range(40):
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            bounds = ax.get_window_extent(renderer)
            if horizontal:
                edge = max(t.get_window_extent(renderer).x1 for t in labels)
                overflow = edge + padding - bounds.x1
                if overflow <= 0:
                    break
                lo, hi = ax.get_xlim()
                ax.set_xlim(lo, hi + (hi - lo) * (overflow / bounds.width + 0.01))
            else:
                edge = max(t.get_window_extent(renderer).y1 for t in labels)
                overflow = edge + padding - bounds.y1
                if overflow <= 0:
                    break
                lo, hi = ax.get_ylim()
                ax.set_ylim(lo, hi + (hi - lo) * (overflow / bounds.height + 0.01))
        else:
            raise RuntimeError("Bar labels could not be fitted inside the axes")


def save_fig(fname):
    fig = plt.gcf()
    # Bar-end annotations belong inside the axes; do not let tight_layout
    # compensate for their overflow by shrinking the plotting rectangle.
    for ax in fig.axes:
        if any(isinstance(c, BarContainer) for c in ax.containers):
            for label in ax.texts:
                label.set_in_layout(False)
    plt.tight_layout(pad=0.3)
    fit_bar_labels(fig)
    path = os.path.join(FIG_DIR, fname)
    plt.savefig(path, dpi=500, bbox_inches="tight", pad_inches=0.05)
    # PDF vector export for IST submission
    pdf_path = os.path.join(FIG_DIR, os.path.splitext(fname)[0] + ".pdf")
    plt.savefig(pdf_path, bbox_inches="tight", pad_inches=0.05)
    plt.close()
    print(f"  -> {fname}")

FORM_LABELS = {
    "ToolAugmented_DomainSystem": "Domain-Tool\nAugmentation",
    "MultiAgent_CollaborationSystem": "Multi-Agent\nCollaboration",
    "SoftwareEngineering_AgenticSystem": "Software Engineering",
    "DigitalEnvironment_OperationSystem": "Digital Environment\nOperation",
    "ResearchAutomation_System": "Research Automation",
    "Data_Database_AgenticSystem": "Data & Database",
    "WorkflowOriented_AgenticSystem": "Workflow-Oriented",
    "DomainSpecific_AgentPlatform": "Domain-Specific\nPlatforms",
    "SearchDriven_AgenticSystem": "Search-Driven",
    "Security_Privacy_AgenticSystem": "Security & Privacy",
}

def domain_label(name):
    special = {"cad_cae_simulation": "CAD/CAE & Simulation",
               "gui_device_automation": "GUI & Device Automation",
               "network_telecom": "Network & Telecom"}
    return special.get(name.lower(), name.replace("_", " ").title())

# ---- Load metadata ----
with open(os.path.join(DATA_DIR, "metadata.json"), encoding="utf-8") as f:
    meta = json.load(f)
N = meta["N"]

# ---- Unified color palette ----
C_PRIMARY = "#4472C4"       # primary bar color
C_ACCENT  = "#E69F00"       # accent / highlight
C_POS     = "#009E73"       # positive / tier-1
C_WARN    = "#E69F00"       # middle tier
C_NEG     = "#999999"       # negative / tier-3
C_PURPLE  = "#8E24AA"       # special / publication types
C_EVOL_YES = "#009E73"      # system evolution: yes
C_EVOL_NO  = "#999999"      # system evolution: no

# ============================================================
# RQ1-1: Feature Frequencies
# ============================================================
def draw_rq1_frequencies():
    data = read_csv("rq1_frequencies.csv")
    lookup = {d["feature"]: d for d in data}
    vals = [int(lookup[k]["count"]) for k in RQ1_KEYS]
    colors = [C_POS if v / N > 0.87 else C_WARN if v / N >= 0.70 else C_NEG for v in vals]

    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    bars = ax.barh(range(len(RQ1_LABELS)), vals, color=colors)
    ax.set_yticks(range(len(RQ1_LABELS)))
    ax.set_yticklabels(RQ1_LABELS, fontsize=10)
    ax.set_xlabel("Papers")
    ax.invert_yaxis()
    for bar, v in zip(bars, vals):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height() / 2,
                f"{v} ({v/N*100:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(right=max(vals) * 1.18)
    save_fig("rq1_frequencies.png")

# ============================================================
# RQ1-2: Feature Co-occurrence Matrix
# ============================================================
def draw_rq1_cooccurrence():
    data = read_csv("rq1_cooccurrence.csv")
    cooc = np.zeros((10, 10), dtype=float)
    for d in data:
        i = RQ1_KEYS.index(d["feature_i"])
        j = RQ1_KEYS.index(d["feature_j"])
        cooc[i][j] = float(d["jaccard"])

    fig, ax = plt.subplots(figsize=(6.3, 5.5))
    im = ax.imshow(cooc, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    ax.set_xticklabels([k.replace("\n", " ") for k in RQ1_LABELS],
                       rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels([k.replace("\n", " ") for k in RQ1_LABELS], fontsize=9)
    plt.colorbar(im, ax=ax, label="Jaccard coefficient")
    save_fig("rq1_cooccurrence.png")

# ============================================================
# RQ1-3: Feature Count Distribution
# ============================================================
def draw_rq1_feature_count():
    data = read_csv("rq1_feature_count.csv")
    xs = [int(d["num_features"]) for d in data]
    ys = [int(d["count"]) for d in data]
    median = np.median([x for x, y in zip(xs, ys) for _ in range(y)]).item() if sum(ys) > 0 else 0

    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.bar(xs, ys, color=C_PRIMARY)
    ax.set_xlabel("Number of Features")
    ax.set_ylabel("Papers")
    save_fig("rq1_feature_count.png")

# ============================================================
# RQ2-1: System Form Distribution
# ============================================================
def draw_rq2_forms():
    data = read_csv("rq2_distribution.csv")
    # sort by primary_count descending
    data.sort(key=lambda d: int(d["primary_count"]), reverse=True)
    labels = [FORM_LABELS[d["form"]] for d in data]
    vals = [int(d["primary_count"]) for d in data]

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.barh(range(len(labels)), vals, color=C_PRIMARY)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Papers")
    ax.invert_yaxis()
    for i, v in enumerate(vals):
        ax.text(v + 1, i, f"{v} ({v/N*100:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(right=max(vals) * 1.18)
    save_fig("rq2_forms.png")

# ============================================================
# RQ2-2: System Form x Application Domain
# ============================================================
def draw_rq2_forms_domain():
    fd_data = read_csv("rq2_domain_cross.csv")
    domains_data = read_csv("rq3_domains.csv")
    forms_data = read_csv("rq2_distribution.csv")

    top_domains = [d["domain"] for d in domains_data[:10]]
    # sort forms by primary_count desc
    forms_data.sort(key=lambda d: int(d["primary_count"]), reverse=True)
    top_forms = [d["form"] for d in forms_data[:8]]

    # build lookup: (form, domain) -> count
    lookup = {}
    for d in fd_data:
        lookup[(d["form"], d["domain"])] = int(d["count"])

    matrix = [[lookup.get((f, d), 0) for d in top_domains] for f in top_forms]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    im = ax.imshow(matrix, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(top_domains)))
    ax.set_yticks(range(len(top_forms)))
    ax.set_xticklabels([domain_label(d) for d in top_domains], rotation=45, ha="right", fontsize=10)
    ax.set_yticklabels([FORM_LABELS[f] for f in top_forms], fontsize=10)
    plt.colorbar(im, ax=ax, label="Papers")
    save_fig("rq2_forms_domain.png")

# ============================================================
# RQ3-1: Application Domains
# ============================================================
def draw_rq3_domains():
    data = read_csv("rq3_domains.csv")
    labels = [domain_label(d["domain"]) for d in data]
    vals = [int(d["count"]) for d in data]

    fig, ax = plt.subplots(figsize=(6.3, 4.5))
    ax.barh(range(len(labels)), vals, color=C_PRIMARY)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Papers")
    ax.invert_yaxis()
    for i, v in enumerate(vals):
        ax.text(v + 1, i, f"{v} ({v/N*100:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(right=max(vals) * 1.18)
    save_fig("rq3_domains.png")

# ============================================================
# RQ3-2: Domain x Feature Prevalence
# ============================================================
def draw_rq3_domain_features():
    data = read_csv("rq3_domain_features.csv")
    domains_data = read_csv("rq3_domains.csv")
    top_domains = [d["domain"] for d in domains_data[:12]]
    domain_n = {d["domain"]: int(d["count"]) for d in domains_data}

    # build matrix: domain x feature, raw counts
    lookup = {}
    for d in data:
        lookup[(d["domain"], d["feature"])] = int(d["count"])

    matrix = []
    for d in top_domains:
        row = [lookup[(d, k.replace("RQ1_", ""))] for k in RQ1_KEYS]
        row_pct = [v / domain_n[d] * 100 for v in row]
        matrix.append(row_pct)

    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
    ax.set_xticks(range(len(RQ1_KEYS)))
    ax.set_yticks(range(len(top_domains)))
    ax.set_xticklabels([k.replace("\n", " ") for k in RQ1_LABELS],
                       rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels([f"{domain_label(d)} (n={domain_n[d]})" for d in top_domains], fontsize=10)
    plt.colorbar(im, ax=ax, label="Papers within domain (%)")
    save_fig("rq3_domain_features.png")

# ============================================================
# RQ4-1: Evaluation Types
# ============================================================
def draw_rq4_evaluation():
    data = read_csv("rq4_evaluation.csv")
    display_labels = {
        "benchmark": "Benchmark", "ablation": "Ablation",
        "experiment": "Other experiments", "case_study": "Case study",
        "human_evaluation": "Human evaluation",
        "real_world_deployment": "Real-world deployment",
        "user_study": "User study", "expert_evaluation": "Expert evaluation",
    }
    labels = [display_labels[d["type"]] for d in data]
    vals = [int(d["count"]) for d in data]

    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.barh(range(len(labels)), vals, color=C_PRIMARY)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Papers")
    ax.invert_yaxis()
    for i, v in enumerate(vals):
        ax.text(v + 1, i, f"{v} ({v/N*100:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(right=max(vals) * 1.27)
    save_fig("rq4_evaluation.png")

# ============================================================
# RQ4-2: Reproducibility
# ============================================================
def draw_rq4_reproducibility():
    data = read_csv("rq4_reproducibility.csv")
    colors_r = {"yes": C_POS, "partial": C_WARN, "no": C_NEG}

    fig, ax = plt.subplots(figsize=(3.8, 3.2))
    for i, d in enumerate(data):
        k, v = d["status"], int(d["count"])
        ax.bar(i, v, color=colors_r.get(k, "#999"), width=0.4)
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels([f"{d['status']}\n({d['count']}, {int(d['count'])/N*100:.0f}%)" for d in data])
    save_fig("rq4_reproducibility.png")

# ============================================================
# Year Trends
# ============================================================
def draw_year_trends():
    data = read_csv("year_trends.csv")
    yx = [d["year"] if d["year"] != "2026" else "2026\n(Jan--Jun)" for d in data]
    yv = [int(d["count"]) for d in data]

    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.plot(yx, yv, marker="o", color=C_PRIMARY, linewidth=2)
    ax.set_xlabel("Year")
    ax.set_ylabel("Papers")
    save_fig("year_trends.png")

# ============================================================
# Publication Types
# ============================================================
def draw_publication_types():
    data = read_csv("publication_stats.csv")
    labels = [d["type"].replace("_", " ").title() if d["type"].strip()
              else "Not recorded" for d in data]
    vals = [int(d["count"]) for d in data]

    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.bar(range(len(labels)), vals, color=C_PURPLE, width=0.4)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([f"{k}\n({v}, {v/N*100:.1f}%)" for k, v in zip(labels, vals)], fontsize=9)
    ax.set_ylabel("Papers")
    save_fig("publication_types.png")

# ============================================================
# Architecture (Diagram Types + System Evolution)
# ============================================================
def draw_architecture_diagram_types():
    diag_data = read_csv("diagram_types.csv")
    diag_labels = [d["type"] for d in diag_data]
    diag_vals = [int(d["count"]) for d in diag_data]

    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.barh(range(len(diag_labels)), diag_vals, color=C_PRIMARY)
    ax.set_yticks(range(len(diag_labels)))
    ax.set_yticklabels(diag_labels, fontsize=10)
    ax.set_xlabel("Papers")
    ax.invert_yaxis()
    for i, v in enumerate(diag_vals):
        ax.text(v + 1, i, f"{v} ({v/N*100:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(right=max(diag_vals) * 1.18)
    save_fig("architecture_diagram_types.png")


def draw_architecture_evolution():
    evol_data = read_csv("system_evolution.csv")
    yes_count = sum(int(d["count"]) for d in evol_data if d["status"].startswith("yes"))
    no_count = sum(int(d["count"]) for d in evol_data if d["status"] == "no")
    N = yes_count + no_count

    labels = [f"Yes\n({yes_count}, {yes_count/N*100:.1f}%)",
              f"No\n({no_count}, {no_count/N*100:.1f}%)"]
    sizes = [yes_count, no_count]
    colors = [C_EVOL_YES, C_EVOL_NO]

    fig, ax = plt.subplots(figsize=(4.0, 3.4))
    wedges, texts = ax.pie(sizes, labels=labels, colors=colors,
                           startangle=90, textprops={"fontsize": 10})
    ax.set_aspect("equal")
    save_fig("architecture_evolution.png")

# ============================================================
# Cross: Human-Collaboration x Evaluation Methods
# ============================================================
def draw_rq1_human_eval_cross():
    data = read_csv("rq1_human_eval_cross.csv")
    with_human = next(d for d in data if d["group"] == "with_human_collab")
    without_human = next(d for d in data if d["group"] == "without_human_collab")

    human_pcts = [float(with_human["user_study_pct"]), float(with_human["human_evaluation_pct"])]
    no_human_pcts = [float(without_human["user_study_pct"]), float(without_human["human_evaluation_pct"])]

    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    x_labels = ["User Study", "Human Evaluation"]
    x = range(len(x_labels))
    w = 0.35

    bars1 = ax.bar([i - w/2 for i in x], human_pcts, w,
                   label=f"With Human-Collab (n={with_human['n']})", color=C_POS)
    bars2 = ax.bar([i + w/2 for i in x], no_human_pcts, w,
                   label=f"Without Human-Collab (n={without_human['n']})", color=C_NEG)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=12)
    ax.set_ylabel("Percentage of Papers (%)")
    ax.legend(fontsize=10)
    for bar, pct in zip(bars1, human_pcts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{pct:.1f}%", ha="center", fontsize=10, fontweight="bold")
    for bar, pct in zip(bars2, no_human_pcts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{pct:.1f}%", ha="center", fontsize=10, fontweight="bold")
    save_fig("rq1_human_eval_cross.png")

# ============================================================
# Cross: System Forms x Evaluation Methods
# ============================================================
def draw_rq2_forms_eval_cross():
    data = read_csv("rq2_forms_eval_cross.csv")
    top_forms = ["ToolAugmented_DomainSystem", "MultiAgent_CollaborationSystem",
                 "SoftwareEngineering_AgenticSystem", "DigitalEnvironment_OperationSystem",
                 "ResearchAutomation_System"]
    top_evals = ["benchmark", "ablation", "experiment", "case_study",
                 "real_world_deployment", "user_study"]
    form_labels = [FORM_LABELS[f] for f in top_forms]
    eval_labels = ["Benchmark", "Ablation", "Experiment", "Case Study",
                   "Real-World\nDeployment", "User Study"]

    lookup = {}
    for d in data:
        lookup[(d["form"], d["eval_type"])] = float(d["pct"])

    matrix = [[lookup[(f, ev)] for ev in top_evals] for f in top_forms]

    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=80)
    ax.set_xticks(range(len(eval_labels)))
    ax.set_yticks(range(len(form_labels)))
    ax.set_xticklabels(eval_labels, fontsize=10)
    ax.set_yticklabels(form_labels, fontsize=10)
    plt.colorbar(im, ax=ax, label="%")
    for i in range(len(form_labels)):
        for j in range(len(eval_labels)):
            val = matrix[i][j]
            color = "white" if val > 40 else "black"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                    fontsize=9, color=color, fontweight="bold")
    save_fig("rq2_forms_eval_cross.png")

# ============================================================
# Main
# ============================================================
ALL_FIGURES = {
    "rq1": [draw_rq1_frequencies, draw_rq1_cooccurrence, draw_rq1_feature_count],
    "rq2": [draw_rq2_forms, draw_rq2_forms_domain],
    "rq3": [draw_rq3_domains, draw_rq3_domain_features],
    "rq4": [draw_rq4_evaluation, draw_rq4_reproducibility],
    "cross": [draw_rq1_human_eval_cross, draw_rq2_forms_eval_cross],
    "trends": [draw_year_trends, draw_publication_types],
    "arch": [draw_architecture_diagram_types, draw_architecture_evolution],
}

if __name__ == "__main__":
    skip = set()
    only = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--skip" and i + 1 < len(args):
            skip.add(args[i + 1])
            i += 2
        elif args[i] == "--only" and i + 1 < len(args):
            only = args[i + 1]
            i += 2
        else:
            i += 1

    if only:
        if only not in ALL_FIGURES:
            print(f"Unknown group: {only}. Available: {list(ALL_FIGURES.keys())}")
            sys.exit(1)
        for fn in ALL_FIGURES[only]:
            fn()
    else:
        for group, funcs in ALL_FIGURES.items():
            if group in skip:
                print(f"SKIP: {group}")
                continue
            for fn in funcs:
                fn()

    print(f"\nDone! All figures saved to {FIG_DIR}/")
