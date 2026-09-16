"""
UI Refinement Styles - DemandWise v2.1
Enhanced animations, glassmorphism, and super-polished UI elements
"""

def get_refinement_css():
    """Return advanced UI refinement CSS for premium appearance."""
    return """
    <style>
        /* ===== HERO ANIMATIONS ===== */
        @keyframes float-in {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes glow-pulse {
            0%, 100% {
                box-shadow: 0 0 20px rgba(30, 136, 229, 0.2), 0 0 40px rgba(30, 136, 229, 0.1);
            }
            50% {
                box-shadow: 0 0 30px rgba(30, 136, 229, 0.4), 0 0 60px rgba(30, 136, 229, 0.2);
            }
        }

        @keyframes slide-right {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes shimmer-load {
            0% {
                background-position: -1000px 0;
            }
            100% {
                background-position: 1000px 0;
            }
        }

        /* ===== CARD ENHANCEMENTS ===== */
        .premium-card {
            background: linear-gradient(135deg, rgba(30, 136, 229, 0.08) 0%, rgba(244, 161, 29, 0.04) 100%);
            border: 1px solid rgba(30, 136, 229, 0.15);
            border-radius: 16px;
            padding: 1.75rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2), 
                        inset 0 1px 0 rgba(255, 255, 255, 0.05);
            position: relative;
            overflow: hidden;
            transition: all 300ms cubic-bezier(0.23, 1, 0.32, 1);
        }

        .premium-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(30, 136, 229, 0.3), transparent);
            opacity: 0;
            transition: opacity 300ms ease;
        }

        .premium-card:hover {
            background: linear-gradient(135deg, rgba(30, 136, 229, 0.12) 0%, rgba(244, 161, 29, 0.08) 100%);
            border-color: rgba(30, 136, 229, 0.25);
            transform: translateY(-8px);
            box-shadow: 0 12px 32px rgba(30, 136, 229, 0.25),
                        0 -1px 0 rgba(255, 255, 255, 0.08),
                        inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }

        .premium-card:hover::before {
            opacity: 1;
        }

        /* ===== STAT DISPLAY ===== */
        .stat-value {
            font-size: 2.8rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #42A5F5 0%, #F4A11D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
        }

        .stat-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #6B7280;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }

        .stat-change {
            font-size: 0.9rem;
            font-weight: 600;
            margin-top: 0.75rem;
        }

        .stat-change.positive {
            color: #10B981;
        }

        .stat-change.negative {
            color: #EF4444;
        }

        /* ===== BUTTON ENHANCEMENTS ===== */
        .enhanced-btn {
            position: relative;
            padding: 0.875rem 2rem;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 250ms cubic-bezier(0.23, 1, 0.32, 1);
            overflow: hidden;
            background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3), 
                        inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }

        .enhanced-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(30, 136, 229, 0.4),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
            filter: brightness(1.15);
        }

        .enhanced-btn:active {
            transform: translateY(-1px);
            box-shadow: 0 2px 10px rgba(30, 136, 229, 0.3);
        }

        /* ===== SECTION DIVIDER ===== */
        .premium-divider {
            margin: 3rem 0;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent 0%, 
                rgba(30, 136, 229, 0.2) 25%,
                rgba(30, 136, 229, 0.3) 50%,
                rgba(30, 136, 229, 0.2) 75%,
                transparent 100%);
        }

        /* ===== METRIC CARDS ===== */
        .metric-card {
            background: linear-gradient(135deg, #1E2537 0%, #252D3D 100%);
            border: 1px solid rgba(30, 136, 229, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: all 250ms ease;
            position: relative;
        }

        .metric-card::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 12px;
            opacity: 0;
            background: radial-gradient(600px at var(--mouse-x, 50%) var(--mouse-y, 50%), 
                rgba(30, 136, 229, 0.1), transparent 80%);
            pointer-events: none;
            transition: opacity 200ms ease;
        }

        .metric-card:hover {
            border-color: rgba(30, 136, 229, 0.2);
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(30, 136, 229, 0.15);
        }

        /* ===== INPUT REFINEMENTS ===== */
        .refined-input {
            background: linear-gradient(135deg, rgba(30, 30, 40, 0.8), rgba(35, 35, 50, 0.8));
            border: 1.5px solid rgba(30, 136, 229, 0.1);
            border-radius: 10px;
            padding: 0.85rem 1.25rem;
            color: white;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 250ms ease;
            backdrop-filter: blur(10px);
        }

        .refined-input:focus {
            border-color: rgba(30, 136, 229, 0.5);
            background: linear-gradient(135deg, rgba(30, 40, 60, 0.9), rgba(40, 50, 70, 0.9));
            box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.15),
                        inset 0 1px 2px rgba(255, 255, 255, 0.05);
            outline: none;
        }

        /* ===== CHART WRAPPER ===== */
        .chart-wrapper {
            background: linear-gradient(135deg, rgba(30, 37, 55, 0.5) 0%, rgba(25, 30, 50, 0.5) 100%);
            border: 1px solid rgba(30, 136, 229, 0.12);
            border-radius: 14px;
            padding: 1.75rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(5px);
            overflow: hidden;
        }

        /* ===== STATUS INDICATOR ===== */
        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: glow-pulse 2s ease-in-out infinite;
        }

        .status-dot.online {
            background: #10B981;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }

        .status-dot.offline {
            background: #F59E0B;
            box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
        }

        /* ===== FADE IN ANIMATIONS ===== */
        .fade-in {
            animation: fadeIn 500ms ease-in-out;
        }

        .fade-in-delay-1 { animation-delay: 100ms; }
        .fade-in-delay-2 { animation-delay: 200ms; }
        .fade-in-delay-3 { animation-delay: 300ms; }
        .fade-in-delay-4 { animation-delay: 400ms; }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* ===== HOVER LIFT EFFECT ===== */
        .hover-lift {
            transition: all 300ms cubic-bezier(0.23, 1, 0.32, 1);
        }

        .hover-lift:hover {
            transform: translateY(-6px);
            box-shadow: 0 20px 40px rgba(30, 136, 229, 0.2);
        }

        /* ===== GRADIENT TEXT ===== */
        .gradient-title {
            background: linear-gradient(135deg, #42A5F5 0%, #F4A11D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        /* ===== BADGE REFINEMENT ===== */
        .refined-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid;
            backdrop-filter: blur(5px);
            transition: all 200ms ease;
        }

        .refined-badge.success {
            background: rgba(16, 185, 129, 0.15);
            color: #10B981;
            border-color: rgba(16, 185, 129, 0.3);
        }

        .refined-badge.success:hover {
            background: rgba(16, 185, 129, 0.25);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
        }

        .refined-badge.warning {
            background: rgba(245, 158, 11, 0.15);
            color: #F59E0B;
            border-color: rgba(245, 158, 11, 0.3);
        }

        .refined-badge.warning:hover {
            background: rgba(245, 158, 11, 0.25);
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
        }

        /* ===== RESPONSIVE AND PERFORMANCE ===== */
        .stButton > button,
        input,
        textarea,
        select,
        [data-testid="stSidebarNav"] a {
            transition: color 180ms ease, background-color 180ms ease,
                        border-color 180ms ease, box-shadow 180ms ease,
                        transform 180ms ease;
        }

        [data-testid="stHorizontalBlock"] {
            gap: clamp(0.75rem, 2vw, 2rem);
        }

        @media (max-width: 900px) {
            .block-container {
                padding: 1.75rem 1.25rem 2.5rem 1.25rem;
            }

            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap;
                row-gap: 1rem;
            }

            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                min-width: calc(50% - 0.5rem);
            }

            .card,
            .kpi-card,
            .glass-card,
            .chart-wrapper {
                padding: 1.25rem;
            }
        }

        @media (max-width: 640px) {
            .block-container {
                padding: 1rem 0.75rem 1.5rem 0.75rem;
            }

            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                min-width: 100%;
            }

            .kpi-card,
            .card,
            .glass-card,
            .chart-wrapper {
                border-radius: 10px;
                padding: 1rem;
            }

            .premium-card:hover,
            .metric-card:hover,
            .hover-lift:hover {
                transform: none;
            }

            .glass-card,
            .chart-wrapper,
            .refined-input,
            .refined-badge {
                backdrop-filter: none;
            }

            .stButton > button {
                min-height: 2.75rem;
                width: 100%;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            .premium-card:hover,
            .metric-card:hover,
            .hover-lift:hover {
                transform: none;
            }

            .glass-card,
            .chart-wrapper,
            .refined-input,
            .refined-badge {
                backdrop-filter: none;
            }
        }
    </style>
    """
