"""
DemandWise - Premium SaaS Theme and Design System
Dark-first design with warm food-inspired accents, smooth animations, and enterprise-grade styling.
"""

# === PREMIUM COLOR PALETTE ===
COLORS = {
    # Dark Surfaces
    'bg_dark_primary': '#0F1419',
    'bg_dark_secondary': '#1A1F2E',
    'bg_dark_tertiary': '#252D3D',
    'surface_dark': '#1E2537',
    'surface_light': '#2A3344',
    
    # Primary Brand Color
    'primary': '#1E88E5',
    'primary_dark': '#0D47A1',
    'primary_light': '#42A5F5',
    'primary_ultra_light': '#E3F2FD',
    
    # Warm Accents (Food-inspired)
    'accent_saffron': '#F4A11D',
    'accent_saffron_light': '#FFC857',
    'accent_green': '#2E7D32',
    'accent_green_light': '#66BB6A',
    'accent_coral': '#E63946',
    
    # Semantic
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'info': '#3B82F6',
    
    # Text
    'text_primary': '#FFFFFF',
    'text_secondary': '#B3BAC2',
    'text_muted': '#6B7280',
    'text_inverse': '#0F1419',
    
    # Borders
    'border_dark': '#3D4556',
    'border_subtle': '#2A3344',
    'divider': '#1E2537',
    
    # Gradients
    'gradient_primary': 'linear-gradient(135deg, #1E88E5 0%, #1565C0 100%)',
    'gradient_saffron': 'linear-gradient(135deg, #F4A11D 0%, #E89012 100%)',
    'gradient_success': 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
}

FONTS = {
    'display': '"Poppins", "Inter", "Segoe UI", sans-serif',
    'primary': '"Inter", "Segoe UI", "-apple-system", sans-serif',
    'mono': '"JetBrains Mono", "Fira Code", monospace',
}


def get_plotly_theme() -> dict:
    """Return the shared Plotly layout styling for DemandWise charts."""
    return {
        'template': 'plotly_dark',
        'paper_bgcolor': COLORS['surface_dark'],
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {
            'family': FONTS['primary'],
            'color': COLORS['text_primary'],
        },
        'colorway': [
            COLORS['primary_light'],
            COLORS['accent_saffron'],
            COLORS['success'],
            COLORS['accent_coral'],
            COLORS['info'],
        ],
        'hoverlabel': {
            'bgcolor': COLORS['surface_light'],
            'font': {'color': COLORS['text_primary']},
        },
        'legend': {
            'font': {'color': COLORS['text_secondary']},
        },
    }

def get_custom_css() -> str:
    """Return comprehensive premium CSS with animations, responsive design, accessibility."""
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {{
            --bg-dark-primary: {COLORS['bg_dark_primary']};
            --bg-dark-secondary: {COLORS['bg_dark_secondary']};
            --bg-dark-tertiary: {COLORS['bg_dark_tertiary']};
            --surface-dark: {COLORS['surface_dark']};
            --surface-light: {COLORS['surface_light']};
            
            --primary: {COLORS['primary']};
            --primary-dark: {COLORS['primary_dark']};
            --primary-light: {COLORS['primary_light']};
            --primary-ultra-light: {COLORS['primary_ultra_light']};
            
            --accent-saffron: {COLORS['accent_saffron']};
            --accent-green: {COLORS['accent_green']};
            --accent-coral: {COLORS['accent_coral']};
            
            --success: {COLORS['success']};
            --warning: {COLORS['warning']};
            --danger: {COLORS['danger']};
            --info: {COLORS['info']};
            
            --text-primary: {COLORS['text_primary']};
            --text-secondary: {COLORS['text_secondary']};
            --text-muted: {COLORS['text_muted']};
            
            --border-dark: {COLORS['border_dark']};
            --border-subtle: {COLORS['border_subtle']};
            
            --transition-fast: 150ms ease-in-out;
            --transition-normal: 250ms ease-in-out;
            --transition-smooth: 350ms cubic-bezier(0.4, 0, 0.2, 1);
        }}

        /* ===== GLOBAL BASE ===== */
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; padding: 0; font-family: {FONTS['primary']}; }}
        body {{ background-color: var(--bg-dark-primary); color: var(--text-primary); }}

        /* Main container */
        .main {{
            background: linear-gradient(135deg, var(--bg-dark-primary) 0%, var(--bg-dark-secondary) 100%);
            padding: 0;
            overflow-x: hidden;
        }}

        .block-container {{
            max-width: 1600px;
            padding: 3rem 3rem 4rem 3rem;
            margin: 0 auto;
        }}

        @media (max-width: 1024px) {{
            .block-container {{ padding: 2rem 2rem 3rem 2rem; max-width: 100%; }}
        }}

        @media (max-width: 640px) {{
            .block-container {{ padding: 1.5rem 1rem 2rem 1rem; }}
        }}

        /* ===== TYPOGRAPHY ===== */
        h1, h2, h3, h4, h5, h6 {{ 
            font-family: {FONTS['display']}; 
            color: var(--text-primary); 
            letter-spacing: -0.02em;
        }}

        h1 {{
            font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}

        h2 {{
            font-size: 1.875rem; font-weight: 600; color: var(--primary);
            margin-top: 2rem; margin-bottom: 1rem;
        }}

        h3 {{ font-size: 1.5rem; font-weight: 600; margin: 1.5rem 0 0.75rem 0; }}

        p, .stMarkdown {{ 
            color: var(--text-secondary); 
            line-height: 1.6;
        }}

        small {{ color: var(--text-muted); font-size: 0.875rem; }}

        /* ===== CARDS ===== */
        .card, .stMetric {{
            background: var(--surface-dark);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border-dark);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transition: all var(--transition-normal);
        }}

        .card:hover, .stMetric:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(30, 136, 229, 0.2);
            border-color: var(--primary-light);
        }}

        /* ===== KPI CARD (Custom) ===== */
        .kpi-card {{
            background: linear-gradient(135deg, var(--surface-dark) 0%, var(--surface-light) 100%);
            border: 1px solid var(--border-dark);
            border-radius: 14px;
            padding: 1.75rem;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            transition: all var(--transition-smooth);
            overflow: hidden;
        }}

        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
            opacity: 0;
            transition: opacity var(--transition-normal);
        }}

        .kpi-card:hover {{
            transform: translateY(-6px);
            box-shadow: 0 12px 32px rgba(30, 136, 229, 0.25);
        }}

        .kpi-card:hover::before {{ opacity: 1; }}

        .kpi-label {{
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}

        .kpi-value {{
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--primary-light);
            font-family: {FONTS['display']};
            letter-spacing: -0.02em;
        }}

        .kpi-delta {{
            font-size: 0.85rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }}

        .kpi-delta.positive {{ color: var(--success); }}
        .kpi-delta.negative {{ color: var(--danger); }}
        .kpi-delta.neutral {{ color: var(--text-muted); }}

        /* ===== STATUS BADGES ===== */
        .badge {{
            display: inline-block;
            padding: 0.375rem 0.875rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .badge-success {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .badge-warning {{
            background: rgba(245, 158, 11, 0.15);
            color: var(--warning);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}

        .badge-danger {{
            background: rgba(239, 68, 68, 0.15);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .badge-saffron {{
            background: rgba(244, 161, 29, 0.15);
            color: var(--accent-saffron);
            border: 1px solid rgba(244, 161, 29, 0.3);
        }}

        /* ===== BUTTONS ===== */
        .stButton > button {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: var(--text-primary);
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-family: {FONTS['primary']};
            transition: all var(--transition-fast);
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.35);
            cursor: pointer;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(30, 136, 229, 0.5);
            filter: brightness(1.1);
        }}

        .stButton > button:active {{
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(30, 136, 229, 0.3);
        }}

        /* ===== FORMS ===== */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stDateInput > div > div > input,
        .stNumberInput > div > div > input {{
            background: var(--surface-dark) !important;
            border: 1.5px solid var(--border-dark) !important;
            border-radius: 8px !important;
            padding: 0.75rem 1rem !important;
            color: var(--text-primary) !important;
            font-family: {FONTS['primary']} !important;
            transition: all var(--transition-fast) !important;
        }}

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stDateInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {{
            border-color: var(--primary-light) !important;
            box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.2) !important;
        }}

        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--surface-dark) 0%, var(--surface-light) 100%);
            border-right: 1px solid var(--border-dark);
        }}

        [data-testid="stSidebar"] h2 {{
            color: var(--primary-light);
            font-size: 1.75rem;
            font-weight: 700;
            padding: 1rem 0;
        }}

        [data-testid="stSidebar"] .stRadio > label {{
            font-weight: 500;
            color: var(--text-secondary);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            transition: all var(--transition-fast);
        }}

        [data-testid="stSidebar"] .stRadio > label:hover {{
            background: rgba(30, 136, 229, 0.15);
            color: var(--primary-light);
        }}

        /* ===== TABLES ===== */
        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}

        .stDataFrame thead tr th {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: var(--text-primary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.875rem;
            letter-spacing: 0.05em;
            padding: 1rem;
        }}

        .stDataFrame tbody tr {{
            border-bottom: 1px solid var(--border-subtle);
        }}

        .stDataFrame tbody tr:hover {{
            background: rgba(30, 136, 229, 0.08);
        }}

        /* ===== CHARTS ===== */
        .stPlotlyChart {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            background: var(--surface-dark);
            padding: 1.5rem;
            border: 1px solid var(--border-dark);
        }}

        /* ===== EXPANDERS ===== */
        .streamlit-expanderHeader {{
            background: var(--surface-dark);
            border: 1px solid var(--border-dark);
            border-radius: 8px;
            font-weight: 600;
            color: var(--text-secondary);
            padding: 1rem;
            transition: all var(--transition-fast);
        }}

        .streamlit-expanderHeader:hover {{
            background: rgba(30, 136, 229, 0.15);
            color: var(--primary-light);
            border-color: var(--primary-light);
        }}

        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem;
            background: transparent;
            border-radius: 0;
            padding: 1rem 0;
            border-bottom: 2px solid var(--border-dark);
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 0;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 3px solid transparent;
            transition: all var(--transition-fast);
        }}

        .stTabs [aria-selected="true"] {{
            color: var(--primary-light);
            border-bottom-color: var(--primary-light);
        }}

        /* ===== ALERTS ===== */
        .stAlert {{
            border-radius: 8px;
            border-left: 4px solid var(--primary);
            padding: 1rem;
            background: rgba(30, 136, 229, 0.1);
        }}

        .stSuccess {{ border-left-color: var(--success); background: rgba(16, 185, 129, 0.1); }}
        .stWarning {{ border-left-color: var(--warning); background: rgba(245, 158, 11, 0.1); }}
        .stError {{ border-left-color: var(--danger); background: rgba(239, 68, 68, 0.1); }}

        /* ===== MISC ===== */
        hr {{
            margin: 2rem 0;
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border-dark), transparent);
        }}

        .stSpinner > div {{ border-top-color: var(--primary-light); }}

        /* ===== CUSTOM UTILITIES ===== */
        .gradient-text {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent-saffron) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }}

        .divider-subtle {{
            height: 1px;
            background: var(--border-subtle);
            margin: 1.5rem 0;
        }}

        /* ===== ACCESSIBILITY ===== */
        @media (prefers-reduced-motion: reduce) {{
            * {{ animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }}
        }}

        /* ===== RESPONSIVE ===== */
        @media (max-width: 768px) {{
            h1 {{ font-size: 2rem; }}
            h2 {{ font-size: 1.5rem; }}
            h3 {{ font-size: 1.25rem; }}
            .kpi-value {{ font-size: 1.75rem; }}
        }}

        @media (max-width: 480px) {{
            .block-container {{ padding: 1rem 0.75rem; }}
            h1 {{ font-size: 1.5rem; }}
            h2 {{ font-size: 1.25rem; }}
            .kpi-value {{ font-size: 1.5rem; }}
            .stButton > button {{ padding: 0.65rem 1.25rem; font-size: 0.9rem; }}
        }}

        /* ===== ADVANCED ANIMATIONS ===== */
        @keyframes slideInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        @keyframes shimmer {{
            0% {{ background-position: -1000px 0; }}
            100% {{ background-position: 1000px 0; }}
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}

        @keyframes glow {{
            0%, 100% {{ box-shadow: 0 0 5px rgba(30, 136, 229, 0.2); }}
            50% {{ box-shadow: 0 0 20px rgba(30, 136, 229, 0.5); }}
        }}

        /* ===== GLASSMORPHISM CARDS ===== */
        .glass-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all var(--transition-smooth);
        }}

        .glass-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(30, 136, 229, 0.3);
            box-shadow: 0 12px 48px rgba(30, 136, 229, 0.2);
        }}

        /* ===== ENHANCED BUTTONS ===== */
        .stButton > button {{
            position: relative;
            overflow: hidden;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            font-size: 0.9rem;
        }}

        .stButton > button::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.15);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }}

        .stButton > button:hover::before {{
            width: 300px;
            height: 300px;
        }}

        /* ===== ENHANCED FORM INPUTS ===== */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stDateInput > div > div > input,
        .stNumberInput > div > div > input {{
            letter-spacing: 0.3px;
        }}

        .stTextInput > label,
        .stSelectbox > label,
        .stDateInput > label,
        .stNumberInput > label {{
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}

        /* ===== LOADING ANIMATION ===== */
        .stProgress > div > div > div > div {{
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent-saffron) 100%);
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(30, 136, 229, 0.3);
        }}

        /* ===== METRIC ENHANCEMENT ===== */
        .stMetricDelta {{
            color: var(--success);
            font-weight: 600;
        }}

        .stMetric [data-testid="metricDeltaContainer-up"] {{
            color: var(--success);
        }}

        .stMetric [data-testid="metricDeltaContainer-down"] {{
            color: var(--danger);
        }}

        /* ===== PLACEHOLDER STATES ===== */
        .empty-state {{
            text-align: center;
            padding: 3rem 1rem;
            background: rgba(30, 136, 229, 0.05);
            border: 2px dashed var(--border-dark);
            border-radius: 16px;
            color: var(--text-muted);
        }}

        .empty-state-icon {{
            font-size: 3.5rem;
            margin-bottom: 1rem;
            animation: bounce 2s ease-in-out infinite;
        }}

        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}

        /* ===== SCROLLER STYLING ===== */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: var(--bg-dark-primary);
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--border-dark);
            border-radius: 4px;
            transition: background var(--transition-fast);
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--primary-light);
        }}

        @media (max-width: 480px) {{
            h1 {{ font-size: 1.5rem; }}
            h2 {{ font-size: 1.25rem; }}
            .kpi-value {{ font-size: 1.5rem; }}
            .stButton > button {{ width: 100%; }}
        }}
    </style>
    """
