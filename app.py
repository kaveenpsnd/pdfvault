import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz, utils
import urllib.parse
import requests
import re
import html


def sanitize_filename(raw_name: str) -> str:
    """Unescape HTML entities repeatedly and strip HTML/div fragments in many encoded forms."""
    if raw_name is None:
        return ''
    s = str(raw_name)
    # Unescape HTML entities multiple times to handle double-encoding
    for _ in range(4):
        s = html.unescape(s)

    # Remove common numeric entity forms like &#60; and variations
    s = re.sub(r'&#\s*0*6?0?;?', '', s)

    # Remove encoded or literal div tags in many variants
    s = re.sub(r'(?i)(?:&lt;|&amp;lt;|<|\\u003c)\s*/?\s*div[^>;&]*?(?:&gt;|&amp;gt;|>|;)?', '', s)

    # Remove any remaining entity-encoded tags
    s = re.sub(r'(?i)&lt;[^&]+&gt;', '', s)

    # Remove any normal HTML tags
    s = re.sub(r'<[^>]+>', '', s)

    # Trim whitespace
    return s.strip()


# Page configuration
st.set_page_config(
    page_title="Past Paper Vault",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def get_pdf_icon_svg():
    """Return PDF icon SVG"""
    return """
    <svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="60" height="60" rx="8" fill="#db463b"/>
        <path d="M18 15h14l8 8v22H18V15z" fill="white"/>
        <path d="M32 15v8h8" stroke="#db463b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M22 28h16M22 35h12M22 42h16" stroke="#09262e" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """


# Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=Poppins:wght@300;400;500;600&display=swap');
    
    .main {
        background-color: #09262e;
        padding: 2rem;
        font-family: 'Poppins', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stTextInput>div>div>input {
        background-color: #ffffff;
        color: #09262e;
        border-radius: 8px;
        border: 2px solid #db463b;
        font-family: 'Poppins', sans-serif;
        font-size: 16px;
        padding: 12px;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #db463b;
        box-shadow: 0 0 0 3px rgba(219, 70, 59, 0.1);
    }
    
    .stButton>button {
        background-color: #db463b;
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        font-size: 16px;
        padding: 12px 24px;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #c03a2b;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(219, 70, 59, 0.3);
    }
    
    .stDownloadButton>button {
        background-color: #28a745;
        color: white;
    }
    
    .stDownloadButton>button:hover {
        background-color: #218838;
    }
    
    .pdf-tile {
        background: rgba(255,255,255,0.02);
        border-radius: 12px;
        padding: 18px;
        margin: 10px 0;
        transition: all 0.18s;
        border: 1px solid rgba(255,255,255,0.03);
    }

    .pdf-tile:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
        border-color: rgba(219, 70, 59, 0.25);
    }

    .pdf-icon {
        width: 60px;
        height: 60px;
        margin: 0 auto 12px;
        display: block;
        text-align: center;
    }

    .pdf-name {
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
        font-size: 15px;
        color: #ffffff;
        text-align: center;
        margin-bottom: 8px;
        line-height: 1.3;
        min-height: 40px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    h1 {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 3rem;
        letter-spacing: 2px;
    }
    
    @media (max-width: 768px) {
        .main {
            padding: 1rem;
        }
        h1 {
            font-size: 2rem;
        }
        .pdf-tile {
            margin: 5px;
            padding: 15px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_master_index():
    """Load the master index CSV file with caching for performance."""
    try:
        csv_path = 'master_index.csv'
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        
        # Normalize column names
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'file' in col_lower and 'name' in col_lower:
                column_mapping[col] = 'File Name'
            elif 'file' in col_lower and 'id' in col_lower:
                column_mapping[col] = 'File ID'
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        if 'File Name' not in df.columns and len(df.columns) >= 1:
            df = df.rename(columns={df.columns[0]: 'File Name'})
        if 'File ID' not in df.columns and len(df.columns) >= 2:
            df = df.rename(columns={df.columns[1]: 'File ID'})
        
        return df
    except FileNotFoundError:
        st.error("❌ master_index.csv file not found!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading master_index.csv: {str(e)}")
        return pd.DataFrame()


def normalize_text(text):
    """Normalize text for better matching."""
    if not text:
        return ""
    text = str(text).lower()
    # Normalize exam levels
    text = re.sub(r'\ba/l\b', 'al', text, flags=re.IGNORECASE)
    text = re.sub(r'\ba\s*l\b', 'al', text, flags=re.IGNORECASE)
    text = re.sub(r'\badvanced?\s+level\b', 'al', text, flags=re.IGNORECASE)
    text = re.sub(r'\bo/l\b', 'ol', text, flags=re.IGNORECASE)
    text = re.sub(r'\bo\s*l\b', 'ol', text, flags=re.IGNORECASE)
    text = re.sub(r'\bordinary\s+level\b', 'ol', text, flags=re.IGNORECASE)
    # Replace separators with spaces
    text = re.sub(r'[_\-\.,;:()\[\]{}]', ' ', text)
    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def fuzzy_search(query, df, limit=50):
    """Perform intelligent fuzzy search with PRIORITY: Subject > Year > Medium > Type > Word Count."""
    if df.empty or query.strip() == "":
        return pd.DataFrame()
    
    # Find the file name column
    file_name_col = None
    for col in df.columns:
        if 'file' in col.lower() and 'name' in col.lower():
            file_name_col = col
            break
    
    if file_name_col is None:
        file_name_col = df.columns[0]
    
    query_lower = normalize_text(query)
    query_words = set(query_lower.split())
    
    # Extract year patterns from query
    query_years = set(re.findall(r'\b(19\d{2}|20\d{2})\b', query))
    
    # Define categories with priority weights
    subjects = ['physics', 'chemistry', 'biology', 'mathematics', 'maths', 'combined', 'commerce', 'history', 'geography', 'economics', 'accounting', 'english', 'sinhala', 'tamil', 'science', 'ict', 'technology', 'buddhism', 'hinduism', 'islam', 'christianity', 'art', 'music', 'drama', 'dancing', 'agriculture', 'business']
    mediums = ['sinhala', 'tamil', 'english']
    levels = ['al', 'ol', 'grade']
    doc_types = ['marking', 'scheme', 'paper', 'pastpaper', 'past']
    
    # Extract query components
    query_subjects = set([word for word in query_words if word in subjects])
    query_mediums = set([word for word in query_words if word in mediums])
    query_levels = set([word for word in query_words if word in levels])
    query_doc_types = set([word for word in query_words if word in doc_types])
    
    # Calculate scores with PRIORITY SYSTEM
    scored_results = []
    for idx, row in df.iterrows():
        filename = str(row[file_name_col])
        filename_lower = normalize_text(filename)
        filename_words = set(filename_lower.split())
        
        # Extract components from filename
        file_years = set(re.findall(r'\b(19\d{2}|20\d{2})\b', filename_lower))
        file_subjects = set([word for word in filename_words if word in subjects])
        file_mediums = set([word for word in filename_words if word in mediums])
        file_levels = set([word for word in filename_words if word in levels])
        file_doc_types = set([word for word in filename_words if word in doc_types])
        
        # ===== PRIORITY SCORING SYSTEM =====
        # Using multiplicative weights for strong priority enforcement
        
        # 1. SUBJECT MATCH (HIGHEST PRIORITY) - Weight: 10000
        subject_score = 0
        if query_subjects:
            matching_subjects = query_subjects & file_subjects
            if matching_subjects:
                subject_score = 10000 * (len(matching_subjects) / len(query_subjects))
        
        # 2. YEAR MATCH (SECOND PRIORITY) - Weight: 1000
        year_score = 0
        if query_years:
            if file_years & query_years:  # Exact year match
                year_score = 1000
            elif file_years:  # Different year
                # Calculate year proximity (closer years get higher scores)
                query_year = int(list(query_years)[0])
                closest_file_year = min(file_years, key=lambda y: abs(int(y) - query_year))
                year_diff = abs(int(closest_file_year) - query_year)
                year_score = max(0, 1000 - (year_diff * 100))  # 100 points penalty per year difference
        
        # 3. MEDIUM MATCH (THIRD PRIORITY) - Weight: 100
        medium_score = 0
        if query_mediums:
            matching_mediums = query_mediums & file_mediums
            if matching_mediums:
                medium_score = 100 * (len(matching_mediums) / len(query_mediums))
        
        # 4. DOCUMENT TYPE MATCH (FOURTH PRIORITY) - Weight: 10
        doc_type_score = 0
        if query_doc_types:
            matching_types = query_doc_types & file_doc_types
            if matching_types:
                doc_type_score = 10 * (len(matching_types) / len(query_doc_types))
        
        # 5. LEVEL MATCH - Weight: 5
        level_score = 0
        if query_levels:
            matching_levels = query_levels & file_levels
            if matching_levels:
                level_score = 5 * (len(matching_levels) / len(query_levels))
        
        # 6. OVERALL WORD MATCH COUNT - Weight: 1
        common_words = query_words & filename_words
        word_match_score = len(common_words)
        
        # 7. BASE FUZZY SCORE (normalized to 0-1 range)
        fuzzy_score = fuzz.token_sort_ratio(query_lower, filename_lower) / 100.0
        
        # TOTAL SCORE with clear priority hierarchy
        total_score = (
            subject_score +      # 10000 scale
            year_score +         # 1000 scale
            medium_score +       # 100 scale
            doc_type_score +     # 10 scale
            level_score +        # 5 scale
            word_match_score +   # 1 scale
            fuzzy_score          # 0-1 scale
        )
        
        # Only include results with some relevance
        if total_score > 5 or (query_subjects and subject_score > 0):
            scored_results.append({
                'index': idx,
                'score': total_score,
                'filename': filename,
                'subject_score': subject_score,
                'year_score': year_score,
                'medium_score': medium_score
            })
    
    # Sort by total score (automatically prioritizes subject > year > medium > type)
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    top_results = scored_results[:limit]
    
    if not top_results:
        return pd.DataFrame()
    
    # Get corresponding rows
    top_indices = [r['index'] for r in top_results]
    results = df.loc[top_indices].copy()
    
    # Add match scores for display
    score_dict = {r['filename']: r['score'] for r in top_results}
    results['Match Score'] = results[file_name_col].map(score_dict)
    
    # Normalize display score to 0-100 for better UX
    max_score = results['Match Score'].max() if not results.empty else 1
    results['Match Score'] = (results['Match Score'] / max_score * 100).round(1)
    
    results = results.sort_values('Match Score', ascending=False)
    
    return results


def get_telegram_file_content(file_id, bot_token):
    """Download file content from Telegram and return bytes."""
    try:
        # Validate inputs
        if not bot_token:
            return None, "❌ Telegram Bot Token not configured."
        
        file_id_str = str(file_id).strip()
        if not file_id_str:
            return None, "❌ Invalid file ID: File ID is empty."
        
        # Get file path from Telegram
        api_url = f"https://api.telegram.org/bot{bot_token}/getFile"
        params = {"file_id": file_id_str}
        
        response = requests.get(api_url, params=params, timeout=10)
        result = response.json()
        
        if not result.get("ok"):
            error_description = result.get("description", "Unknown error")
            error_code = result.get("error_code", "N/A")
            return None, f"❌ Telegram API error ({error_code}): {error_description}"
        
        file_path = result["result"]["file_path"]
        
        # Download the file content
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        file_response = requests.get(download_url, timeout=30)
        file_response.raise_for_status()
        
        return file_response.content, None
    
    except requests.exceptions.Timeout:
        return None, "❌ Request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return None, f"❌ Network error: {str(e)}"
    except KeyError as e:
        return None, f"❌ Unexpected API response format: {str(e)}"
    except Exception as e:
        return None, f"❌ Error downloading file: {str(e)}"


def main():
    # Initialize session state
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'download_cache' not in st.session_state:
        st.session_state.download_cache = {}
    
    # Title
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-family: 'Barlow Condensed', sans-serif; font-weight: 700; color: #ffffff; font-size: 3.5rem; letter-spacing: 3px; margin-bottom: 0.5rem;">📚 PAST PAPER VAULT</h1>
        <p style="font-family: 'Poppins', sans-serif; color: #db463b; font-size: 1rem; font-weight: 400; letter-spacing: 1px; margin-top: 0;">powered by <strong>Examlanka.lk</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for bot token
    try:
        bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            st.error("❌ Telegram Bot Token not configured. Please add it to .streamlit/secrets.toml")
            st.stop()
    except Exception as e:
        st.error(f"❌ Error accessing secrets: {str(e)}")
        st.stop()
    
    # Load data
    df = load_master_index()
    
    if df.empty:
        st.warning("⚠️ No data available. Please ensure master_index.csv is present.")
        return
    
    # Get query parameter from URL
    query_params = st.query_params
    url_query = query_params.get("q", "")
    if url_query:
        url_query = urllib.parse.unquote_plus(url_query)
        if url_query != st.session_state.search_query:
            st.session_state.search_query = url_query
    
    # Search interface
    col1, col2, col3, col4 = st.columns([1, 4, 0.8, 1])
    with col2:
        search_query = st.text_input(
            "Search",
            value=st.session_state.search_query,
            placeholder="Search for past papers... (e.g., physics 2021, mathematics, chemistry)",
            key="search_input",
            label_visibility="collapsed"
        )
    with col3:
        st.write("")
        search_button = st.button(
            "🔍 Search",
            key="search_btn",
            use_container_width=True,
            type="primary"
        )
    
    # Handle search
    if search_button or search_query != st.session_state.search_query:
        st.session_state.search_query = search_query
        st.session_state.download_cache = {}  # Clear download cache on new search
    
    # Display results
    if st.session_state.search_query:
        with st.spinner('🔍 Searching for your past papers... Please wait'):
            results = fuzzy_search(st.session_state.search_query, df, limit=30)

        if not results.empty:
            file_name_col = [col for col in results.columns if 'file' in col.lower() and 'name' in col.lower()]
            file_id_col = [col for col in results.columns if 'file' in col.lower() and 'id' in col.lower()]

            file_name_col = file_name_col[0] if file_name_col else results.columns[0]
            file_id_col = file_id_col[0] if file_id_col else results.columns[1]

            num_cols = 3
            cols = st.columns(num_cols)

            for idx, (row_idx, row) in enumerate(results.iterrows()):
                file_name = row[file_name_col]
                file_id = str(row[file_id_col])
                match_score = row.get('Match Score', 0)

                # Clean filename
                raw_name = str(file_name)
                cleaned = sanitize_filename(raw_name)
                display_name = html.escape(cleaned.replace('_', ' ').replace('-', ' '))
                
                col_idx = idx % num_cols

                with cols[col_idx]:
                    # Render tile
                    tile_html = f"""
                    <div class="pdf-tile">
                        <div class="pdf-icon">{get_pdf_icon_svg()}</div>
                        <div class="pdf-name">{display_name}</div>
                        <div style='text-align:center; margin-top:6px;'>
                            <span style='background-color: rgba(219, 70, 59, 0.2); color: #db463b; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;'>Match: {match_score:.1f}%</span>
                        </div>
                    </div>
                    """
                    st.markdown(tile_html, unsafe_allow_html=True)
                    
                    # Download button with caching
                    cache_key = f"file_content_{file_id}"
                    
                    if cache_key in st.session_state.download_cache:
                        # File already downloaded, show download button
                        file_content, error = st.session_state.download_cache[cache_key]
                        if error:
                            st.error(error)
                        else:
                            filename = cleaned if cleaned.lower().endswith('.pdf') else f"{cleaned}.pdf"
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=file_content,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"download_{file_id}_{idx}"
                            )
                    else:
                        # Prepare download button
                        if st.button("📥 Prepare Download", key=f"prepare_{file_id}_{idx}", use_container_width=True):
                            with st.spinner("⏳ Preparing your download... Please wait"):
                                file_content, error = get_telegram_file_content(file_id, bot_token)
                                st.session_state.download_cache[cache_key] = (file_content, error)
                                st.rerun()
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #ffffff;">
                <h2 style="font-family: 'Barlow Condensed', sans-serif; font-size: 2rem; margin-bottom: 1rem;">🔍 No Results Found</h2>
                <p style="font-family: 'Poppins', sans-serif; font-size: 1.1rem;">Try a different search query</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Welcome message
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #ffffff;">
            <h2 style="font-family: 'Barlow Condensed', sans-serif; font-size: 2.5rem; margin-bottom: 1rem; letter-spacing: 2px;">Welcome to Past Paper Vault</h2>
            <p style="font-family: 'Poppins', sans-serif; font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9;">Search for past papers by subject, year, or school</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistics
        st.markdown("""
        <style>
        .stMetric {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid rgba(219, 70, 59, 0.3);
        }
        .stMetric label {
            color: #ffffff;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
        }
        .stMetric [data-testid="stMetricValue"] {
            color: #db463b;
            font-family: 'Barlow Condensed', sans-serif;
            font-weight: 700;
            font-size: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Papers", len(df))
        with col2:
            try:
                unique_count = df['File Name'].nunique() if 'File Name' in df.columns else len(df)
            except:
                unique_count = len(df)
            st.metric("Unique Files", unique_count)
        with col3:
            st.metric("Status", "🟢 Active")


if __name__ == "__main__":
    main()
