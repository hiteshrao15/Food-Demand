# DemandWise Component & Theme Reference

Quick reference for developers extending the DemandWise UI.

## 🎨 Color System

### Usage
```python
from src.styles.theme import COLORS, FONTS

# Access colors
primary_color = COLORS['primary']           # #1E88E5
bg_dark = COLORS['bg_dark_primary']         # #0F1419
success_green = COLORS['success']            # #10B981
```

### Color Categories

#### Surfaces & Backgrounds
- `bg_dark_primary`: #0F1419 (main background)
- `surface_dark`: #1A1F2E (cards)
- `surface_elevated`: #252D3D (elevated cards)
- `border_dark`: #2A3344 (borders)
- `border_subtle`: #3A4354 (subtle borders)

#### Primary Colors
- `primary`: #1E88E5 (main brand)
- `primary_dark`: #0D47A1 (hover/dark)
- `primary_light`: #42A5F5 (disabled/light)

#### Semantic Colors
- `success`: #10B981 (positive, ready)
- `warning`: #F59E0B (caution, attention)
- `danger`: #EF4444 (critical, error)
- `info`: #0EA5E9 (neutral info)

#### Food & Business Accents
- `accent_saffron`: #F4A11D (warm, food)
- `accent_green`: #2E7D32 (fresh, positive)
- `accent_coral`: #E63946 (demand, alert)

#### Text Colors
- `text_primary`: #FFFFFF (main text)
- `text_secondary`: #B3BAC2 (secondary text)
- `text_muted`: #6B7280 (muted text)

---

## 🔤 Typography

### Usage
```python
from src.styles.theme import FONTS

# Access fonts
display = FONTS['display']      # Poppins (bold headings)
body = FONTS['body']            # Inter (body text)
mono = FONTS['mono']            # JetBrains Mono (code)
```

### Font System

#### Poppins (Display - Headings)
- Weight: 700 (bold)
- Usage: H1-H3 headlines, big numbers
- Import: Google Fonts

#### Inter (Body - Main Text)
- Weight: 400-600
- Usage: Body text, labels, buttons
- Import: Google Fonts

#### JetBrains Mono (Mono - Code)
- Weight: 400
- Usage: Data values, timestamps, code
- Import: Google Fonts

---

## 🧩 Component Library

### KPI Card
Premium metric display with optional delta indicator.

```python
from src.ui.components import render_kpi_card

html = render_kpi_card(
    label="Daily Demand",
    value="247 units",
    delta="+12%",                    # Optional
    delta_type="positive",           # "positive", "negative", "neutral"
    icon="📦",                       # Unicode emoji
    color_accent=COLORS['primary']   # Optional override
)
st.markdown(html, unsafe_allow_html=True)
```

**Features**:
- Animated hover effect (translateY -4px)
- Color-coded delta indicator
- Flexible sizing
- Responsive

**CSS Classes**:
- `.kpi-card` - Main container
- `.kpi-value` - Value text
- `.kpi-delta` - Delta badge

---

### Data Card
Information display with icon and optional footer.

```python
from src.ui.components import render_data_card

html = render_data_card(
    title="Model Status",
    content="Random Forest ready",
    icon="🤖",
    footer="Last trained: 2h ago",
    color="success"                  # "primary", "success", "warning", "danger"
)
st.markdown(html, unsafe_allow_html=True)
```

**Features**:
- Left-border accent color
- Icon support
- Footer separator
- Responsive

---

### Status Card
Key-value pair display with status indicator.

```python
from src.ui.components import render_status_card

html = render_status_card(
    title="System Status",
    status="active",                 # "active", "warning", "offline"
    items={
        "Model": "Ready ✓",
        "Data": "365 days",
        "Last Update": "2 hours ago"
    }
)
st.markdown(html, unsafe_allow_html=True)
```

---

### Top Bar
Page header with title, icon, and optional subtitle.

```python
from src.ui.components import render_top_bar

render_top_bar(
    page_title="Forecast Demand",
    page_icon="🔮",
    subtitle="AI-powered demand prediction",
    action_button=None               # Optional: {"label": "New", "callback": None}
)
```

---

### Status Badge
Semantic colored badge.

```python
from src.ui.components import render_status_badge

# Returns HTML string
badge = render_status_badge(
    status="success",                # "success", "warning", "danger", "info", "saffron"
    label="Ready to Deploy",
    size="md"                        # "sm", "md", "lg"
)
st.markdown(badge, unsafe_allow_html=True)
```

---

### Section Header
Section divider with icon and title.

```python
from src.ui.components import section_header

section_header(
    title="Key Drivers",
    subtitle="What influences this forecast",  # Optional
    icon="📊"
)
```

---

### Divider
Subtle gradient separator.

```python
from src.ui.components import divider

divider()  # No parameters
```

---

### Empty State
Placeholder for empty/no-data scenarios.

```python
from src.ui.components import empty_state

empty_state(
    icon="🔮",
    title="No Forecasts Yet",
    message="Configure parameters and generate your first forecast",
    action_text="Create Forecast"   # Optional
)
```

---

### Error State
Error display with recovery guidance.

```python
from src.ui.components import error_state

error_state(
    icon="⚠️",
    title="Data Connection Failed",
    message="Unable to load historical data. Check your connection and try again."
)
```

---

### Success State
Success confirmation display.

```python
from src.ui.components import success_state

success_state(
    icon="✓",
    title="Forecast Saved",
    message="Your prediction has been saved and added to history."
)
```

---

### Loading Skeleton
Animated placeholder for loading content.

```python
from src.ui.components import loading_skeleton

loading_skeleton(height="100px")  # CSS height value
```

---

### Form Group
Label for form inputs with required indicator.

```python
from src.ui.components import render_form_group

render_form_group(
    label="Food Item",
    required=True,
    help_text="Select the food item to forecast"
)
```

---

## 🎨 CSS Custom Properties

Available in all `<style>` blocks:

```css
:root {
  /* Colors */
  --bg-dark-primary: #0F1419;
  --primary: #1E88E5;
  --success: #10B981;
  --warning: #F59E0B;
  --danger: #EF4444;
  --text-primary: #FFFFFF;
  
  /* Animations */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms cubic-bezier(0.23, 1, 0.320, 1);
  --transition-smooth: 350ms cubic-bezier(0.165, 0.84, 0.44, 1);
}
```

---

## 🎬 Animation Guidelines

### Duration Standards
- **Fast (150ms)**: Button hovers, badge transitions
- **Normal (250ms)**: Form focus, card expand
- **Smooth (350ms)**: Page transitions, deep interactions

### Accessibility
```css
/* Always include this for accessibility */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Common Patterns

#### Hover Lift
```css
transform: translateY(-4px);
box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
transition: all var(--transition-fast);
```

#### Gradient Text
```css
background: linear-gradient(135deg, #1E88E5 0%, #F4A11D 100%);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```

#### Focus State
```css
border: 2px solid #42A5F5;
box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.15);
transition: all var(--transition-fast);
```

---

## 📱 Responsive Breakpoints

```python
# Applied automatically in theme.css

# Desktop (default)
# 1600px max-width containers

# Tablet
@media (max-width: 1024px)
  # Reduced padding, adjusted font sizes

# Mobile
@media (max-width: 640px)
  # Full-width elements, stacked layouts

# Small Mobile
@media (max-width: 480px)
  # Minimal padding, extra-large touch targets
```

---

## 🔧 Customization Guide

### Changing Primary Color
```python
# In src/styles/theme.py
COLORS = {
    'primary': '#2196F3',  # Change from #1E88E5
    'primary_dark': '#1565C0',
    'primary_light': '#64B5F6',
    # ...
}
```

### Adding Custom Component
```python
# In src/ui/components.py

def render_custom_card(title, content):
    """Custom component following DemandWise patterns."""
    return f"""
    <div style="background: {COLORS['surface_dark']};
                border: 1px solid {COLORS['border_dark']};
                border-radius: 12px;
                padding: 1.5rem;">
        <h3>{title}</h3>
        <p>{content}</p>
    </div>
    """

# Use in pages
html = render_custom_card("Title", "Content")
st.markdown(html, unsafe_allow_html=True)
```

### Overriding Theme CSS
```python
# In any page
import streamlit as st
from src.styles.theme import get_custom_css

# Get default CSS
base_css = get_custom_css()

# Add overrides
custom_css = base_css + """
<style>
.my-custom-class {
    color: #1E88E5;
    font-weight: 700;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)
```

---

## 🏗️ Layout Patterns

### Two-Column Workflow
```python
col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.markdown("### Configuration")
    # Config form

with col2:
    st.markdown("### Results")
    # Results display
```

### KPI Grid
```python
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    render_kpi_card(...)
```

### Sidebar Navigation
```python
st.sidebar.markdown(f"<h2 style='color: {COLORS['primary']}'>DemandWise</h2>", unsafe_allow_html=True)
selected = st.sidebar.radio("Navigate", ["Overview", "Forecast", "Analytics"])
```

---

## 🧪 Testing Components

```python
# Quick test in Streamlit
from src.ui.components import *
from src.styles.theme import COLORS

st.title("Component Gallery")

st.header("KPI Cards")
render_kpi_card("Test", "100", "+5%", "positive", "📊")

st.header("Data Cards")
render_data_card("Title", "Content", "📈", color="success")

st.header("Badges")
st.markdown(render_status_badge("success", "Active"), unsafe_allow_html=True)
```

---

## 📊 Charts Best Practices

### Color Scheme for Charts
```python
import plotly.graph_objects as go
from src.styles.theme import COLORS

fig = go.Figure()
fig.add_trace(go.Bar(
    y=values,
    marker_color=COLORS['primary'],
    hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>'
))

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor=COLORS['surface_dark'],
    font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
    xaxis=dict(showgrid=False, gridwidth=1, gridcolor=COLORS['border_subtle']),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
    height=400,
    margin=dict(l=40, r=20, t=20, b=40),
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
```

---

## 🚀 Performance Tips

### Caching
```python
@st.cache_data
def load_historical_data():
    return DataLoader.load_from_csv()

@st.cache_resource
def get_predictor():
    return DemandPredictor()
```

### Lazy Loading
```python
if st.session_state.get('show_details'):
    render_detailed_chart()  # Only render when needed
```

### State Management
```python
if 'forecast_generated' not in st.session_state:
    st.session_state.forecast_generated = False

if st.button("Generate"):
    st.session_state.forecast_generated = True
```

---

**DemandWise Component Reference** © 2024
