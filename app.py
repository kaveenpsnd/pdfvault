import streamlit as st
import pandas as pd
from rapidfuzz import process
from telegram import Bot
from telegram.error import TelegramError
import urllib.parse
import asyncio
import concurrent.futures
import requests

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

# Custom CSS with new design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=Poppins:wght@300;400;500;600&display=swap');
    
    /* Main styling */
    .main {
        background-color: #09262e;
        padding: 2rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Search bar styling */
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
    
    /* Button styling */
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
    
    /* Search button with icon */
    .search-btn {
        background-color: #db463b;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s;
        cursor: pointer;
    }
    
    .search-btn:hover {
        background-color: #c03a2b;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(219, 70, 59, 0.3);
    }
    
    .search-icon {
        width: 20px;
        height: 20px;
    }
    
    /* Search button icon styling */
    button[kind="secondary"] {
        background-color: #db463b !important;
        color: white !important;
        border: none !important;
    }
    
    button[kind="secondary"]:hover {
        background-color: #c03a2b !important;
    }
    
    /* PDF Tile styling */
    .pdf-tile {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s;
        border: 2px solid transparent;
    }
    
    .pdf-tile:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(219, 70, 59, 0.2);
        border-color: #db463b;
    }
    
    .pdf-icon {
        width: 60px;
        height: 60px;
        margin: 0 auto 15px;
        display: block;
    }
    
    .pdf-name {
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
        font-size: 16px;
        color: #09262e;
        text-align: center;
        margin-bottom: 15px;
        line-height: 1.5;
        min-height: 80px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        display: -webkit-box;
        -webkit-line-clamp: 5;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    .download-btn {
        width: 100%;
        background-color: #db463b;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .download-btn:hover {
        background-color: #c03a2b;
    }
    
    /* Title styling */
    h1 {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 3rem;
        letter-spacing: 2px;
    }
    
    /* Form button styling */
    .stForm {
        background-color: transparent;
    }
    
    .stForm button {
        background-color: #db463b;
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
    }
    
    /* Markdown links */
    a {
        color: #db463b;
        text-decoration: none;
    }
    
    a:hover {
        color: #c03a2b;
        text-decoration: underline;
    }
    
    /* Mobile responsiveness */
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

@st.cache_data(ttl=3600)  # Cache for 1 hour, or clear cache when CSV changes
def load_master_index():
    """Load the master index CSV file with caching for performance."""
    try:
        # Read CSV and get file modification time to invalidate cache on changes
        import os
        csv_path = 'master_index.csv'
        df = pd.read_csv(csv_path)
        # Handle column names with spaces
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        st.error("❌ master_index.csv file not found!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading master_index.csv: {str(e)}")
        return pd.DataFrame()

def fuzzy_search(query, df, limit=5):
    """Perform fuzzy search on File_Name column using RapidFuzz."""
    if df.empty or query.strip() == "":
        return pd.DataFrame()
    
    # Get all file names
    file_names = df['File Name'].tolist()
    
    # Perform fuzzy matching
    matches = process.extract(query, file_names, limit=limit)
    
    # Extract matched file names and their scores
    matched_names = [match[0] for match in matches]
    
    # Filter dataframe to get matched rows
    results = df[df['File Name'].isin(matched_names)].copy()
    
    # Add match scores
    score_dict = {match[0]: match[1] for match in matches}
    results['Match Score'] = results['File Name'].map(score_dict)
    
    # Sort by match score (descending)
    results = results.sort_values('Match Score', ascending=False)
    
    return results

def get_telegram_download_url(file_id):
    """Get the direct download URL for a Telegram file using Bot API."""
    try:
        # Get bot token from Streamlit secrets
        bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            st.error("❌ Telegram Bot Token not configured. Please set it in Streamlit secrets.")
            return None
        
        # Validate file_id
        file_id_str = str(file_id).strip()
        if not file_id_str:
            st.error("❌ Invalid file ID: File ID is empty.")
            return None
        
        # Use Telegram Bot API directly via HTTP
        api_url = f"https://api.telegram.org/bot{bot_token}/getFile"
        params = {"file_id": file_id_str}
        
        response = requests.get(api_url, params=params, timeout=10)
        
        # Get the JSON response to check for errors
        result = response.json()
        
        if not result.get("ok"):
            error_description = result.get("description", "Unknown error")
            error_code = result.get("error_code", "N/A")
            raise Exception(f"Telegram API error ({error_code}): {error_description}")
        
        # If we get here, the request was successful
        response.raise_for_status()
        
        file_path = result["result"]["file_path"]
        
        # Construct direct download URL
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        
        return download_url
    
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        # Try to get more details from the response if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                if not error_data.get("ok"):
                    error_desc = error_data.get("description", "Unknown error")
                    error_code = error_data.get("error_code", "N/A")
                    st.error(f"❌ Telegram API Error ({error_code}): {error_desc}")
                    if "file_id" in error_desc.lower() or "invalid" in error_desc.lower():
                        st.warning("💡 **Note:** File IDs are bot-specific. The file ID must come from a message that your bot has access to.")
                else:
                    st.error(f"❌ Network error: {str(e)}")
            except:
                st.error(f"❌ Network error: {str(e)}")
        else:
            st.error(f"❌ Network error: {str(e)}")
        return None
    except KeyError as e:
        st.error(f"❌ Unexpected API response format: {str(e)}")
        return None
    except Exception as e:
        error_msg = str(e)
        if "Telegram API error" in error_msg:
            # Handle Telegram API errors
            if "file_id" in error_msg.lower() or "invalid" in error_msg.lower():
                st.error(f"❌ Invalid file ID: The file ID '{file_id}' is not a valid Telegram file ID.")
                with st.expander("ℹ️ About Telegram File IDs"):
                    st.markdown("""
                    **Telegram File IDs** are unique identifiers for files in Telegram. They:
                    - Are typically long alphanumeric strings (e.g., `BAACAgIAAxkBAAIBY2Zg...`)
                    - Can sometimes be numeric, but must be valid Telegram file IDs
                    - Can expire or become invalid if files are deleted
                    - Are bot-specific: each bot gets different file IDs for the same file
                    
                    **Possible issues:**
                    1. The file IDs might be from a different bot
                    2. The file IDs might be expired or invalid
                    3. The bot might not have access to these files
                    
                    **Note:** File IDs generated by Telethon's `pack_bot_file_id` should work, 
                    but they need to be used with a bot that has access to the files.
                    """)
            else:
                st.error(f"❌ {error_msg}")
        else:
            st.error(f"❌ Error generating download link: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Error generating download link: {str(e)}")
        st.exception(e)  # Show full traceback for debugging
        return None

def main():
    # Title with subtitle
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-family: 'Barlow Condensed', sans-serif; font-weight: 700; color: #ffffff; font-size: 3.5rem; letter-spacing: 3px; margin-bottom: 0.5rem;">📚 PAST PAPER VAULT</h1>
        <p style="font-family: 'Poppins', sans-serif; color: #db463b; font-size: 1rem; font-weight: 400; letter-spacing: 1px; margin-top: 0;">powered by <strong>Examlanka.lk</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load master index
    df = load_master_index()
    
    if df.empty:
        st.warning("⚠️ No data available. Please ensure master_index.csv is present.")
        return
    
    # Get query parameter from URL
    query_params = st.query_params
    url_query = query_params.get("q", "")
    
    # Decode URL-encoded query
    if url_query:
        url_query = urllib.parse.unquote_plus(url_query)
    
    # Initialize session state for search query
    if 'search_query' not in st.session_state:
        st.session_state.search_query = url_query if url_query else ""
    
    # Update search query if URL parameter is present
    if url_query and url_query != st.session_state.search_query:
        st.session_state.search_query = url_query
    
    # Search interface - centered with search button
    col1, col2, col3, col4 = st.columns([1, 4, 0.8, 1])
    with col2:
        search_query = st.text_input(
            "",
            value=st.session_state.search_query,
            placeholder="Search for past papers... (e.g., physics 2021, mathematics, chemistry)",
            key="search_input",
            label_visibility="collapsed"
        )
    with col3:
        st.write("")  # Spacing
        # Search button with icon
        search_button = st.button(
            "🔍 Search",
            key="search_btn",
            use_container_width=True,
            type="primary"
        )
    
    # Handle search on button click
    if search_button:
        st.session_state.search_query = search_query
        st.rerun()
    
    # Auto-search on input or URL parameter
    if search_query != st.session_state.search_query:
        st.session_state.search_query = search_query
    elif url_query and st.session_state.search_query:
        st.session_state.search_query = url_query
    
    # Display results in grid
    if st.session_state.search_query:
        results = fuzzy_search(st.session_state.search_query, df, limit=20)  # Show more results in grid
        
        if not results.empty:
            # Create grid layout - 3 columns on desktop, 2 on tablet, 1 on mobile
            num_cols = 3
            cols = st.columns(num_cols)
            
            for idx, (row_idx, row) in enumerate(results.iterrows()):
                file_name = row['File Name']
                file_id = str(row['File ID'])
                match_score = row.get('Match Score', 0)
                
                # Show full filename (formatted for readability)
                display_name = file_name.replace('_', ' ').replace('-', ' ')
                
                # Determine which column to use
                col_idx = idx % num_cols
                
                with cols[col_idx]:
                    # PDF Tile
                    st.markdown(f"""
                    <div class="pdf-tile">
                        <div class="pdf-icon">{get_pdf_icon_svg()}</div>
                        <div class="pdf-name">{display_name}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Download button
                    with st.form(key=f"form_{file_id}"):
                        submitted = st.form_submit_button("📥 Download", use_container_width=True)
                        
                        if submitted:
                            download_url = get_telegram_download_url(file_id)
                            if download_url:
                                st.markdown(
                                    f'<a href="{download_url}" download="{file_name}" style="display: inline-block; width: 100%; padding: 0.5rem; background-color: #db463b; color: white; text-align: center; text-decoration: none; border-radius: 0.25rem; font-weight: bold; margin-top: 0.5rem; font-family: \'Barlow Condensed\', sans-serif;">⬇️ Click to Download</a>',
                                    unsafe_allow_html=True
                                )
                            else:
                                st.error("❌ Failed to generate link")
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #ffffff;">
                <h2 style="font-family: 'Barlow Condensed', sans-serif; font-size: 2rem; margin-bottom: 1rem;">🔍 No Results Found</h2>
                <p style="font-family: 'Poppins', sans-serif; font-size: 1.1rem;">Try a different search query</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Welcome message when no query
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #ffffff;">
            <h2 style="font-family: 'Barlow Condensed', sans-serif; font-size: 2.5rem; margin-bottom: 1rem; letter-spacing: 2px;">Welcome to Past Paper Vault</h2>
            <p style="font-family: 'Poppins', sans-serif; font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9;">Search for past papers by subject, year, or school</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show statistics in a nice layout
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
            st.metric("Total Papers", len(df), label_visibility="visible")
        with col2:
            st.metric("Unique Files", df['File Name'].nunique(), label_visibility="visible")
        with col3:
            st.metric("Status", "🟢 Active", label_visibility="visible")

if __name__ == "__main__":
    main()

