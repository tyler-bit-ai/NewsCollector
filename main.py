import streamlit as st
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import datetime
import json

# Local imports
from config import GMAIL_USER, GMAIL_APP_PASSWORD, DEFAULT_RECIPIENTS
from news_collector import NewsCollector
from news_analyzer import NewsAnalyzer

# --- UI Configuration & CSS ---
st.set_page_config(
    page_title="T Roaming MI",
    page_icon="🌐",
    layout="wide"
)

def inject_custom_css():
    st.markdown("""
        <style>
            @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");

            /* Global Font Settings */
            .stApp {
                font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
                color: #333333;
            }
            
            /* Headers */
            h1, h2, h3 { font-family: 'Pretendard', sans-serif !important; }
            h2 { font-size: 20px !important; font-weight: 700 !important; margin-top: 30px !important; color: #1a1a1a; }
            h3 { font-size: 16px !important; font-weight: 600 !important; color: #444; margin-top: 15px !important; }

            /* Executive Summary */
            .exec-summary-box {
                background-color: #FFF8E1; /* Light Yellow */
                border-left: 5px solid #FFC107; /* Amber */
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .exec-title {
                font-weight: 800;
                font-size: 18px;
                color: #B00020; /* Deep Red for Emphasis */
                margin-bottom: 10px;
            }
            .exec-content {
                font-size: 15px;
                line-height: 1.6;
            }

            /* Strategy Box */
            .strategy-box {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-top: 4px solid #E53935; /* SK Red */
                padding: 20px;
                border-radius: 8px;
            }
            
            /* Compact Table Style */
            .report-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #EEE;
                margin-bottom: 10px;
                transition: transform 0.2s;
            }
            .report-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            }
            .card-title {
                font-weight: 700;
                font-size: 15px;
                color: #222;
                text-decoration: none;
                display: block;
                margin-bottom: 5px;
            }
            .card-meta {
                font-size: 11px;
                color: #888;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .card-summary {
                font-size: 13px;
                color: #555;
                line-height: 1.5;
            }
            .badge {
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 10px;
            }
            .badge-naver { background: #03C75A; color: white; }
            .badge-google { background: #4285F4; color: white; }
            .badge-comm { background: #FF5722; color: white; }

        </style>
    """, unsafe_allow_html=True)

def generate_html_email(data, date_str):
    """
    Morning Brew Style HTML Template
    """
    
    # 1. Parsing Data
    summary_raw = data.get("email_top_summary", "")
    summary_html = ""
    if "•" in summary_raw:
        items = [x.strip() for x in summary_raw.split("•") if x.strip()]
        for item in items:
            summary_html += f'<li style="margin-bottom: 8px;">{item}</li>'
        summary_html = f'<ul style="padding-left: 20px; margin: 0;">{summary_html}</ul>'
    else:
        summary_html = f'<p>{summary_raw}</p>'

    strategy_raw = data.get("strategic_insight", "").replace("\n", "<br>")

    def render_section_items(items):
        if not items: return '<p style="color:#999; font-size:13px;">No updates today.</p>'
        html = ""
        for item in items:
            title = item.get("title", "No Title")
            link = item.get("link", "#")
            summary = item.get("summary", "")
            source = item.get("source", "Source")
            
            html += f"""
            <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px dashed #EEE;">
                <div style="font-size: 11px; color: #E53935; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">{source}</div>
                <a href="{link}" style="display: block; font-size: 16px; font-weight: 700; color: #222; text-decoration: none; margin-bottom: 6px;">{title}</a>
                <p style="margin: 0; font-size: 14px; color: #555; line-height: 1.6;">{summary}</p>
            </div>
            """
        return html

    # Sections
    html_market = render_section_items(data.get("section_market_culture", []))
    html_global = render_section_items(data.get("section_global_trend", []))
    html_competitors = render_section_items(data.get("section_competitors", []))
    html_esim_products = render_section_items(data.get("section_esim_products", []))
    html_voc_roaming = render_section_items(data.get("section_voc_roaming", []))
    html_voc_esim = render_section_items(data.get("section_voc_esim", []))

    # HTML Construction
    # Using 'Morning Brew' aesthetic: Clean white, Serif headings (or clean Sans), heavy black headers, blue links etc.
    # But user asked for SKT Brand Colors emphasized + Pretendard.
    
    template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ margin: 0; padding: 0; font-family: 'Pretendard', sans-serif; background-color: #F4F4F4; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #FFFFFF; }}
        .header {{ background-color: #FFFFFF; padding: 30px 20px; border-bottom: 4px solid #E53935; }}
        .logo {{ color: #E53935; font-weight: 900; font-size: 26px; letter-spacing: -1px; }}
        .date {{ color: #888; font-size: 13px; margin-top: 5px; font-weight: 500; }}
        .section-title {{ 
            background-color: #222; color: #FFF; 
            font-size: 16px; font-weight: 700; 
            padding: 8px 15px; margin: 30px 0 20px 0; 
            border-radius: 4px; display: inline-block;
        }}
        .content-box {{ padding: 0 25px; }}
        .insight-box {{ background-color: #FFF8E1; padding: 25px; border-radius: 8px; margin: 20px 25px; border-left: 5px solid #FFC107; }}
        .strategy-box {{ background-color: #FAFAFA; padding: 25px; border-top: 3px solid #E53935; margin: 20px 25px; }}
        .footer {{ background-color: #333; color: #999; padding: 30px; text-align: center; font-size: 12px; }}
        a {{ color: #222; text-decoration: none; }}
        a:hover {{ text-decoration: underline; color: #E53935; }}
    </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div class="logo">T Roaming MI Report</div>
                <div class="date">{date_str} | Daily Business Intelligence</div>
            </div>

            <!-- Executive Summary -->
            <div class="insight-box">
                <div style="font-weight: 800; font-size: 18px; margin-bottom: 15px; color: #333;">📢 Executive Summary</div>
                <div style="font-size: 15px; line-height: 1.7; color: #333;">
                    {summary_html}
                </div>
            </div>

            <!-- Content Sections -->
            <div class="content-box">

                <div class="section-title">0. Market & Culture (Macro)</div>
                {html_market}

                <div class="section-title">1. Global Roaming Trend</div>
                {html_global}

                <div class="section-title">2. SKT & Competitors (KT/LGU+)</div>
                {html_competitors}

                <div class="section-title">3. eSIM</div>
                {html_esim_products}

                <div class="section-title">4. 로밍 VoC</div>
                {html_voc_roaming}

                <div class="section-title">5. eSIM VoC</div>
                {html_voc_esim}

            </div>

            <!-- Strategy -->
            <div class="strategy-box">
                <div style="font-weight: 800; font-size: 18px; margin-bottom: 15px; color: #E53935;">💡 SKT 로밍 전략 제언</div>
                <div style="font-size: 15px; line-height: 1.7; color: #444;">
                    {strategy_raw}
                </div>
            </div>

            <!-- Footer -->
            <div class="footer">
                T Roaming Business Intelligence Bot<br>
                For Internal Use Only - SK Telecom Co., Ltd.
            </div>
        </div>
    </body>
    </html>
    """
    return template

def send_email_via_gmail(recipient_email, subject, html_content):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return False, "Gmail credentials not set."
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Email Error: {str(e)}"

def render_feed_items(items, badge_type="naver"):
    if not items:
        st.caption("데이터가 없습니다.")
        return

    for item in items:
        title = item.get('title')
        link = item.get('link')
        summary = item.get('summary')
        source = item.get('source', 'Unknown')
        
        # UI Card
        st.markdown(f"""
        <div class="report-card">
            <div class="card-meta">
                <span class="badge badge-{badge_type}">{source}</span>
            </div>
            <a href="{link}" target="_blank" class="card-title">{title}</a>
            <div class="card-summary">{summary}</div>
        </div>
        """, unsafe_allow_html=True)


def main():
    inject_custom_css()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("T Roaming Strategic BI")
        st.caption("Integrated Naver & Google Hybrid Intelligence Engine")
    with col2:
        st.markdown(f"<div style='text-align:right; padding-top:20px; font-weight:bold;'>{datetime.date.today()}</div>", unsafe_allow_html=True)
        
    # Initial State
    if 'report_data' not in st.session_state:
        st.session_state.report_data = None
    if 'recipients_status' not in st.session_state:
        st.session_state.recipients_status = {email: True for email in DEFAULT_RECIPIENTS}

    # --- Debug Mode Toggle ---
    with st.sidebar:
        st.markdown("---")
        st.title("⚙️ Settings")
        debug_mode = st.checkbox("🐛 Debug Mode (Show Filter Logs)", value=False)

    # Action Button
    if st.button("🚀 Start Hybrid Data Collection & Analysis", type="primary", use_container_width=True):

        collector = NewsCollector(debug_mode=debug_mode)
        analyzer = NewsAnalyzer()

        with st.status("🔍 Processing Intelligence Cycle...", expanded=True) as status:

            # Step 1: Hybrid Collection
            st.write("📡 Step 1: Collecting data from Naver & Google...")
            raw_data = collector.collect_hybrid()

            d_count = len(raw_data.get('domestic', []))
            g_count = len(raw_data.get('global', []))
            st.write(f"   ✅ Collected: Domestic {d_count}, Global {g_count}")

            # Step 2: AI Analysis
            st.write("🧠 Step 2: GPT-5 Semantic Analysis & Noise Filtering...")
            final_report = analyzer.analyze_and_summarize(raw_data)

            if "error" in final_report:
                st.error(final_report["error"])
                status.update(label="Failed", state="error")
            else:
                st.session_state.report_data = final_report
                status.update(label="Intelligence Cycle Completed!", state="complete", expanded=False)

        # 디버그: 수집된 원본 데이터 출력 (status 블록 밖으로 이동)
        with st.expander("🔍 [DEBUG] Collected Raw Data (Click to View)", expanded=False):
            st.markdown("### Domestic Items")
            for i, item in enumerate(raw_data.get('domestic', [])[:20], 1):  # 상위 20개만
                st.markdown(f"**{i}. [{item.get('source')}] {item.get('title')}**")
                st.caption(f"Link: {item.get('link')}")
                st.caption(f"Published: {item.get('published', 'N/A')}")
                st.markdown("---")

            st.markdown("### Global Items")
            for i, item in enumerate(raw_data.get('global', [])[:20], 1):  # 상위 20개만
                st.markdown(f"**{i}. [{item.get('source')}] {item.get('title')}**")
                st.caption(f"Link: {item.get('link')}")
                st.caption(f"Published: {item.get('published', 'N/A')}")
                st.markdown("---")

        # 디버그: 필터링 사유 상세 표시
        if debug_mode and st.session_state.report_data and 'filter_info' in st.session_state.report_data:
            with st.expander("🔍 [DEBUG] Filtering Details (Why articles were filtered/passed)", expanded=False):
                filter_info = st.session_state.report_data['filter_info']

                # Domestic 필터링 결과
                st.markdown("### 📰 Domestic Articles Filtering")
                domestic_passed = [f for f in filter_info['domestic'] if not f['filtered']]
                domestic_filtered = [f for f in filter_info['domestic'] if f['filtered']]

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"#### ✅ Passed ({len(domestic_passed)})")
                    for f in domestic_passed:
                        st.markdown(f"**{f['title']}...**")
                        st.caption(f"Score: {f['score']} | {f['details']}")
                        st.markdown("---")

                with col2:
                    st.markdown(f"#### ❌ Filtered ({len(domestic_filtered)})")
                    for f in domestic_filtered:
                        st.markdown(f"**{f['title']}...**")
                        st.caption(f"Reason: {f['reason']} | {f['details']}")
                        st.markdown("---")

                # Global 필터링 결과
                st.markdown("### 🌍 Global Articles Filtering")
                global_passed = [f for f in filter_info['global'] if not f['filtered']]
                global_filtered = [f for f in filter_info['global'] if f['filtered']]

                col3, col4 = st.columns(2)
                with col3:
                    st.markdown(f"#### ✅ Passed ({len(global_passed)})")
                    for f in global_passed:
                        st.markdown(f"**{f['title']}...**")
                        st.caption(f"Score: {f['score']} | {f['details']}")
                        st.markdown("---")

                with col4:
                    st.markdown(f"#### ❌ Filtered ({len(global_filtered)})")
                    for f in global_filtered:
                        st.markdown(f"**{f['title']}...**")
                        st.caption(f"Reason: {f['reason']} | {f['details']}")
                        st.markdown("---")

    # --- Result Dashboard ---
    if st.session_state.report_data:
        data = st.session_state.report_data
        
        st.markdown("---")
        
        # 1. Executive Summary
        st.markdown(f"""
        <div class="exec-summary-box">
            <div class="exec-title">🔔 Executive Summary</div>
            <div class="exec-content">{data.get('email_top_summary', '').replace(chr(10), '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Main Columns
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("0. Market & Culture (Macro)")
            render_feed_items(data.get('section_market_culture', []), "naver")

            st.subheader("2. SKT & Competitors (KT/LGU+)")
            render_feed_items(data.get('section_competitors', []), "naver")

            st.subheader("4. 로밍 VoC")
            render_feed_items(data.get('section_voc_roaming', []), "comm")

        with c2:
            st.subheader("1. Global Roaming Trend")
            render_feed_items(data.get('section_global_trend', []), "google")

            st.subheader("3. eSIM")
            render_feed_items(data.get('section_esim_products', []), "naver")

            st.subheader("5. eSIM VoC")
            render_feed_items(data.get('section_voc_esim', []), "comm")
            
        # 3. Strategy
        st.markdown("---")
        st.markdown(f"""
        <div class="strategy-box">
            <h3 style="color:#E53935; margin:0 0 10px 0;">💡 T Roaming Strategic Hints</h3>
            <div style="white-space: pre-line;">{data.get('strategic_insight', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        # --- Email Management ---
        st.markdown("---")
        st.subheader("📤 Report Distribution")
        
        with st.expander("Manage Recipients"):
            cols = st.columns(3)
            current_emails = list(st.session_state.recipients_status.keys())
            for i, email in enumerate(current_emails):
                with cols[i % 3]:
                    st.session_state.recipients_status[email] = st.checkbox(email, value=st.session_state.recipients_status[email], key=email)
        
            new_mail = st.text_input("Add Recipient")
            if st.button("Add"):
                if new_mail and "@" in new_mail:
                    st.session_state.recipients_status[new_mail] = True
                    st.success(f"Added {new_mail}")

        # --- Preview Section (Restored) ---
        with st.expander("🔎 Email Preview (Click to Expand)", expanded=False):
            today_str_preview = datetime.date.today().strftime("%Y-%m-%d")
            preview_html = generate_html_email(data, today_str_preview)
            components.html(preview_html, height=800, scrolling=True)

        if st.button("📧 Send Email via Gmail", use_container_width=True):
            recipients = [e for e, v in st.session_state.recipients_status.items() if v]
            if not recipients:
                st.warning("Select at least one recipient.")
            else:
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                html_body = generate_html_email(data, today_str)
                
                progress = st.progress(0)
                success_n = 0
                for idx, r in enumerate(recipients):
                    ok, msg = send_email_via_gmail(r, f"[T Roaming MI] {today_str} Daily Report", html_body)
                    if ok: success_n += 1
                    progress.progress((idx+1)/len(recipients))
                
                st.success(f"Sent to {success_n} recipients!")

if __name__ == "__main__":
    main()
