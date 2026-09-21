"""Export the same readable coding diagram to PDF, SVG, PNG and editable draw.io.

Only presentation is changed; the worked example retains its existing codes.
Coordinates and font sizes share one specification across the four exports.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent
W, H = 760, 870
INK, BLUE, GREEN = '#1F2937', '#4472C4', '#009E73'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'pdf.fonttype': 42,
                     'svg.fonttype': 'none'})
fig = plt.figure(figsize=(W / 100, H / 100))
ax = fig.add_axes([0, 0, 1, 1])
ax.set(xlim=(0, W), ylim=(H, 0))
ax.axis('off')
mxfile = ET.Element('mxfile', host='app.diagrams.net')
diagram = ET.SubElement(mxfile, 'diagram', id='codmas-coding', name='CODMAS coding example')
model = ET.SubElement(diagram, 'mxGraphModel', page='1', pageWidth=str(W), pageHeight=str(H))
root = ET.SubElement(model, 'root')
ET.SubElement(root, 'mxCell', id='0')
ET.SubElement(root, 'mxCell', id='1', parent='0')

def cell(name, value, style, x, y, w, h):
    c = ET.SubElement(root, 'mxCell', id=name, value=value, style=style, vertex='1', parent='1')
    ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})

def box(name, x, y, w, h, fill='#F8FAFC', stroke=BLUE):
    ax.add_patch(FancyBboxPatch((x,y), w,h, boxstyle='round,pad=0,rounding_size=8',
                               linewidth=1, facecolor=fill, edgecolor=stroke))
    cell(name, '', f'rounded=1;arcSize=8;html=0;fillColor={fill};strokeColor={stroke};',x,y,w,h)

def text(name, value, x, y, w, h, size=18, bold=False, color=INK):
    ax.text(x,y,value,va='top',ha='left',fontsize=size*.72,color=color,
            fontweight='bold' if bold else 'normal', linespacing=1.3)
    cell(name,value,f'text;html=0;whiteSpace=wrap;align=left;verticalAlign=top;spacing=0;'
         f'fontFamily=DejaVu Sans;fontSize={size};fontColor={color};fontStyle={int(bold)};',x,y,w,h)

text('title','Worked coding example: CODMAS',20,12,720,32,24,True)
box('study',20,54,720,104,fill='#EAF0FA')
text('study-title','Source: structured RTL optimization',36,68,680,30,20,True)
text('study-info','Conference paper (2026)\nCoding based on reported full-text descriptions',36,100,680,50)

box('rq1',20,178,720,240,fill='#FFFFFF')
text('rq1-title','RQ1 · Reported characteristics (10/10)',36,192,680,28,20,True)
features = [
    'Perception & context acquisition', 'Reasoning & planning',
    'Action execution', 'Tool & capability use',
    'Memory & state management', 'Environment interaction',
    'Feedback & reflection', 'Human-in-the-loop collaboration',
    'Role & multi-agent coordination', 'Governance & traceability',
]
for i, label in enumerate(features):
    x,y=36+(i%2)*352,231+(i//2)*36
    box(f'feature-box-{i}',x,y,336,29,fill='#E7F4EF',stroke=GREEN)
    text(f'feature-{i}',label,x+8,y+5,322,24,17)
text('rq1-note','All ten characteristics are reported in the source study.',36,425,690,26,18)

box('rq2',20,468,350,160)
box('rq3',390,468,350,160)
text('rq2-title','RQ2 · System form',36,484,318,28,20,True)
text('rq2-body','Primary:\nMulti-Agent Collaboration\nSecondary:\nDomain-Tool-Augmented',36,521,318,100,18)
text('rq3-title','RQ3 · Application domain',406,484,318,28,20,True)
text('rq3-body','Domain: Software Engineering\nTask: RTL optimization',406,529,318,80,18)

box('rq4',20,650,350,198,fill='#FFF8E6',stroke='#E69F00')
box('rq5',390,650,350,198)
text('rq4-title','RQ4 · Evaluation practices',36,667,318,28,20,True)
text('rq4-body','Benchmark; case study;\nexperiment; ablation;\nstatistical analysis\n\nReported artifact availability: No',36,703,318,135,18)
text('rq5-title','RQ5 · Architecture & evolution',406,667,318,28,18,True)
text('rq5-body','Diagrams: system architecture;\nworkflow/flowchart\n\nSystem evolution discussed: Yes',406,710,318,120,18)

for suffix in ('pdf','svg','png'):
    fig.savefig(OUT / f'taxonomic_example.{suffix}', dpi=300, facecolor='white')
plt.close(fig)
ET.indent(mxfile, space='  ')
ET.ElementTree(mxfile).write(OUT/'taxonomic_example.drawio',encoding='utf-8',xml_declaration=True)
print('Exported taxonomic_example: PDF, SVG, PNG, draw.io')
