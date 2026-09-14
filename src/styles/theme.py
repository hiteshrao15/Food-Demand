"""
DemandWise - Professional Theme and Styling
Centralized design system with modern color palette and typography.
"""

# Color Palette - Professional and Modern
COLORS = {
    # Primary Colors
    'primary': '#2E86AB',
    'primary_dark': '#1A5F7A',
    'primary_light': '#5BA4C7',

    # Secondary Colors
    'secondary': '#A23B72',
    'secondary_dark': '#7A2B55',
    'secondary_light': '#C76BA0',

    # Accent Colors
    'success': '#06A77D',
    'warning': '#F18F01',
    'danger': '#C73E1D',
    'info': '#4A90E2',

    # Neutrals
    'background': '#F8F9FA',
    'surface': '#FFFFFF',
    'border': '#E1E8ED',
    'text_primary': '#1A1A2E',
    'text_secondary': '#6C757D',
    'text_muted': '#ADB5BD',
}

# Typography
FONTS = {
    'primary': '"Inter", "Segoe UI", "Roboto", sans-serif',
    'secondary': '"Space Grotesk", "Helvetica Neue", sans-serif',
    'mono': '"JetBrains Mono", "Fira Code", monospace',
}

def get_custom_css() -> str:
    """Return comprehensive custom CSS for Streamlit."""
    return f"""
    <style>
        /* ============================================
           GLOBAL STYLES
        ============================================ */

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');

        :root {{
            --primary: {COLORS['primary']};
            --primary-dark: {COLORS['primary_dark']};
            --primary-light: {COLORS['primary_light']};
            --secondary: {COLORS['secondary']};
            --success: {COLORS['success']};
            --warning: {COLORS['warning']};
            --danger: {COLORS['danger']};
            --info: {COLORS['info']};
            --background: {COLORS['background']};
            --surface: {COLORS['surface']};
            --border: {COLORS['border']};
            --text-primary: {COLORS['text_primary']};
            --text-secondary: {COLORS['text_secondary']};
        }}

        /* Main Container */
        .main {{
            background-color: var(--background);
            padding: 2rem;
        }}

        .block-container {{
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}

        /* ============================================
           TYPOGRAPHY
        ============================================ */

        h1, h2, h3, h4, h5, h6 {{
            font-family: {FONTS['secondary']};
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        h2 {{
            font-size: 1.875rem;
            font-weight: 600;
            color: var(--primary);
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}

        h3 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }}

        p, .stMarkdown {{
            font-family: {FONTS['primary']};
            color: var(--text-secondary);
            line-height: 1.6;
        }}

        /* ============================================
           CARDS AND CONTAINERS
        ============================================ */

        .stMetric {{
            background: var(--surface);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
        }}

        .stMetric:hover {{
            box-shadow: 0 4px 12px rgba(46, 134, 171, 0.15);
            transform: translateY(-2px);
        }}

        .stMetric label {{
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }}

        .stMetric [data-testid="stMetricValue"] {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
            font-family: {FONTS['secondary']};
        }}

        /* Info Box */
        .stInfo {{
            background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
            border-left: 4px solid var(--info);
            border-radius: 8px;
            padding: 1rem;
        }}

        /* Success Box */
        .stSuccess {{
            background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
            border-left: 4px solid var(--success);
            border-radius: 8px;
            padding: 1rem;
        }}

        /* Warning Box */
        .stWarning {{
            background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
            border-left: 4px solid var(--warning);
            border-radius: 8px;
            padding: 1rem;
        }}

        /* Error Box */
        .stError {{
            background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
            border-left: 4px solid var(--danger);
            border-radius: 8px;
            padding: 1rem;
        }}

        /* ============================================
           BUTTONS
        ============================================ */

        .stButton > button {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-family: {FONTS['primary']};
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(46, 134, 171, 0.3);
        }}

        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(46, 134, 171, 0.4);
        }}

        .stButton > button:active {{
            transform: translateY(0);
        }}

        /* Secondary Button */
        .stButton[data-baseweb="button"][kind="secondary"] > button {{
            background: white;
            color: var(--primary);
            border: 2px solid var(--primary);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}

        .stButton[data-baseweb="button"][kind="secondary"] > button:hover {{
            background: var(--primary-light);
            color: white;
            border-color: var(--primary-light);
        }}

        /* ============================================
           INPUTS AND FORMS
        ============================================ */

        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stDateInput > div > div > input {{
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem;
            font-family: {FONTS['primary']};
            transition: all 0.3s ease;
        }}

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stDateInput > div > div > input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(46, 134, 171, 0.1);
        }}

        /* ============================================
           SIDEBAR
        ============================================ */

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--surface) 0%, #F8F9FA 100%);
            border-right: 1px solid var(--border);
        }}

        [data-testid="stSidebar"] h2 {{
            color: var(--primary);
            font-size: 1.75rem;
            font-weight: 700;
            padding: 1rem 0;
        }}

        [data-testid="stSidebar"] .stRadio > label {{
            font-weight: 500;
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.2s ease;
        }}

        [data-testid="stSidebar"] .stRadio > label:hover {{
            background: var(--primary-light);
            color: white;
        }}

        /* ============================================
           DATAFRAMES AND TABLES
        ============================================ */

        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }}

        .stDataFrame thead tr th {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.875rem;
            letter-spacing: 0.05em;
            padding: 1rem;
        }}

        .stDataFrame tbody tr:hover {{
            background: #F8F9FA;
        }}

        /* ============================================
           CHARTS AND PLOTS
        ============================================ */

        .stPlotlyChart {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            background: var(--surface);
            padding: 1rem;
        }}

        /* ============================================
           DIVIDERS
        ============================================ */

        hr {{
            margin: 2rem 0;
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border), transparent);
        }}

        /* ============================================
           EXPANDERS
        ============================================ */

        .streamlit-expanderHeader {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-weight: 600;
            color: var(--text-primary);
            padding: 1rem;
            transition: all 0.3s ease;
        }}

        .streamlit-expanderHeader:hover {{
            background: var(--primary-light);
            color: white;
            border-color: var(--primary-light);
        }}

        /* ============================================
           TABS
        ============================================ */

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem;
            background: var(--surface);
            border-radius: 12px;
            padding: 0.5rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }}

        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
        }}

        /* ============================================
           LOADING AND SPINNERS
        ============================================ */

        .stSpinner > div {{
            border-top-color: var(--primary);
        }}

        /* ============================================
           FOOTER
        ============================================ */

        footer {{
            background: var(--surface);
            border-top: 1px solid var(--border);
            padding: 2rem 0;
            margin-top: 4rem;
        }}

        footer p {{
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        /* ============================================
           CUSTOM CLASSES
        ============================================ */

        .gradient-text {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }}

        .card {{
            background: var(--surface);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
        }}

        .card:hover {{
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
            transform: translateY(-4px);
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .badge-success {{
            background: var(--success);
            color: white;
        }}

        .badge-warning {{
            background: var(--warning);
            color: white;
        }}

        .badge-info {{
            background: var(--info);
            color: white;
        }}

        /* ============================================
           RESPONSIVE DESIGN
        ============================================ */

        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}

            .block-container {{
                padding: 1rem;
            }}

            .stMetric {{
                padding: 1rem;
            }}
        }}

        /* ============================================
           ANIMATIONS
        ============================================ */

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .fade-in {{
            animation: fadeIn 0.5s ease-out;
        }}

        @keyframes slideIn {{
            from {{
                transform: translateX(-20px);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}

        .slide-in {{
            animation: slideIn 0.5s ease-out;
        }}

    </style>
    """


def get_plotly_theme() -> dict:
    """Return custom Plotly theme configuration."""
    return {
        'layout': {
            'font': {
                'family': FONTS['primary'],
                'size': 12,
                'color': COLORS['text_primary']
            },
            'title': {
                'font': {
                    'family': FONTS['secondary'],
                    'size': 20,
                    'color': COLORS['text_primary']
                }
            },
            'paper_bgcolor': COLORS['surface'],
            'plot_bgcolor': COLORS['background'],
            'colorway': [
                COLORS['primary'],
                COLORS['secondary'],
                COLORS['success'],
                COLORS['warning'],
                COLORS['info'],
                COLORS['primary_light'],
                COLORS['secondary_light'],
            ],
            'xaxis': {
                'gridcolor': COLORS['border'],
                'linecolor': COLORS['border'],
            },
            'yaxis': {
                'gridcolor': COLORS['border'],
                'linecolor': COLORS['border'],
            },
        }
    }
