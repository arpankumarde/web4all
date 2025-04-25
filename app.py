import streamlit as st
import matplotlib.pyplot as plt
from main import analyze_accessibility, WebAccessibilityChecker
import base64
from io import BytesIO
import pandas as pd
from urllib.parse import urlparse
import time
import openai
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from dotenv import load_dotenv
import pathlib

# Load environment variables
load_dotenv()

# Create static directory if it doesn't exist
static_dir = pathlib.Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)


# Helper function to load logo and return base64 encoding
def get_logo_base64():
    logo_path = static_dir / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo_data = f.read()
        return base64.b64encode(logo_data).decode()
    return None


# Get logo as base64 for both favicon and header display
logo_b64 = get_logo_base64()

# Set page configuration with logo as favicon if available
if logo_b64:
    favicon = f"data:image/png;base64,{logo_b64}"
else:
    favicon = "♿"  # Default favicon if logo not available

# Set page configuration
st.set_page_config(
    page_title="Web4All Accessibility Checker",
    page_icon=favicon,
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Web4All Accessibility Checker helps evaluate website accessibility."
    },
)


# Helper function to display logo
def display_logo():
    if logo_b64:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <img src="data:image/png;base64,{logo_b64}" alt="Web4All Logo" style="height: 80px; margin-right: 20px;">
                <h1>Web4All Accessibility Checker</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Display a message if logo is missing
        st.warning(f"Logo file not found. Please place a logo.png file in {static_dir}")
        st.title("Web4All Accessibility Checker")


# Set light mode theme
st.markdown(
    """
    <script>
        var elements = window.parent.document.querySelectorAll('.st-emotion-cache-lrlib, .st-emotion-cache-16txtl3');
        elements.forEach(function(element) {
            element.innerHTML = element.innerHTML + '<style>:root{--background-color: #ffffff; --secondary-background-color: #f0f2f6;}</style>';
        });
    </script>
    """,
    unsafe_allow_html=True,
)

# Add custom CSS for styling
st.markdown(
    """
<style>
    .main {
        padding: 2rem;
    }
    .score-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .excellent {color: #28a745;}
    .good {color: #17a2b8;}
    .fair {color: #ffc107;}
    .poor {color: #fd7e14;}
    .very-poor {color: #dc3545;}
    
    .stProgress > div > div > div > div {
        height: 20px;
    }
    
    .category-header {
        font-weight: bold;
        margin-top: 15px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# App header with logo
display_logo()  # Use the new function to display logo

st.markdown(
    """
This tool analyzes web pages for accessibility issues and provides suggestions for improvement.
Enter a URL below to check its accessibility score.
"""
)

# Store analysis results in session state
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
    st.session_state.domain = None
    st.session_state.checker = None
    st.session_state.ai_recommendations = None


def get_score_class(score):
    if score >= 90:
        return "excellent"
    elif score >= 80:
        return "good"
    elif score >= 70:
        return "fair"
    elif score >= 50:
        return "poor"
    else:
        return "very-poor"


# Function to convert matplotlib figure to image for Streamlit
def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", transparent=True)
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode()
    return img_str


# Function to get AI recommendations for accessibility improvements
def get_ai_recommendations(results):
    try:
        # Get OpenAI API key from environment variable or let user input it
        api_key = os.environ.get("OPENAI_API_KEY", None)

        if api_key is None or api_key == "":
            st.warning(
                "OpenAI API key not found. Please enter your API key to get AI recommendations."
            )
            api_key = st.text_input("Enter your OpenAI API key:", type="password")
            if not api_key:
                return None

        # Set up the OpenAI client
        client = openai.OpenAI(api_key=api_key)

        # Create a prompt based on the issues found
        issues_text = ""
        for category, details in results["categories"].items():
            if details["issues"]:
                issues_text += f"\n{category.upper()} ISSUES:\n"
                for issue in details["issues"]:
                    issues_text += f"- {issue}\n"

        prompt = f"""You are a web accessibility expert. Based on the following accessibility issues found on a website, 
        provide 3-5 practical recommendations to improve the website's accessibility:
        
        OVERALL SCORE: {results["total_score"]}/100
        
        ISSUES FOUND: {issues_text}
        
        Please provide specific, actionable recommendations that address the most critical issues first.
        Format your response with markdown headings and bullet points.
        """

        # Make API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a web accessibility expert providing concise, practical recommendations.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        # Extract and return the recommendations
        recommendations = response.choices[0].message.content
        return recommendations

    except Exception as e:
        st.error(f"Error generating AI recommendations: {str(e)}")
        return None


# Function to send email with accessibility report
def send_email_report(recipient_email, domain, results, ai_recommendations=None):
    try:
        # Get SMTP settings from environment variables
        smtp_email = os.environ.get("AWS_SES_SMTP_EMAIL")
        smtp_host = os.environ.get("AWS_SES_SMTP_HOST")
        smtp_port = int(os.environ.get("AWS_SES_SMTP_PORT"))
        smtp_user = os.environ.get("AWS_SES_SMTP_USER")
        smtp_pass = os.environ.get("AWS_SES_SMTP_PASS")

        # Create message container
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Web Accessibility Report for {domain}"
        msg["From"] = smtp_email
        msg["To"] = recipient_email

        # Generate chart for email
        fig = plt.figure(figsize=(8, 6))
        categories = []
        scores = []
        for category, details in results["categories"].items():
            categories.append(category.title())
            scores.append(details["score"] * 100)

        plt.bar(
            categories,
            scores,
            color=["#4CAF50", "#2196F3", "#FFC107", "#FF5722", "#9C27B0"],
        )
        plt.ylim(0, 100)
        plt.title(f"Accessibility Scores for {domain}")
        plt.ylabel("Score (%)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Convert chart to image for email
        img_buf = BytesIO()
        plt.savefig(img_buf, format="png")
        img_buf.seek(0)
        img_data = img_buf.read()
        plt.close(fig)

        # Set a filename for the image attachment
        chart_filename = f"accessibility_chart_{domain}.png"

        # Create HTML content for email
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f2f2f2; padding: 10px; border-radius: 5px; }}
                .score-container {{ background-color: #f8f9fa; border-radius: 10px; padding: 20px; margin: 15px 0; }}
                .category {{ margin-bottom: 15px; }}
                .issues {{ margin-left: 20px; }}
                .excellent {{ color: #28a745; }}
                .good {{ color: #17a2b8; }}
                .fair {{ color: #ffc107; }}
                .poor {{ color: #fd7e14; }}
                .very-poor {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Web Accessibility Report</h1>
                    <p>Website: <strong>{domain}</strong></p>
                    <p>Date: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
                
                <div class="score-container">
                    <h2 class="{get_score_class(results["total_score"])}">
                        Overall Score: {results["total_score"]}/100
                    </h2>
                </div>
                
                <h2>Category Scores</h2>
        """

        # Add category details
        for category, details in results["categories"].items():
            cat_score = int(details["score"] * 100)
            cat_class = get_score_class(cat_score)

            html_content += f"""
                <div class="category">
                    <h3>{category.title()}: <span class="{cat_class}">{cat_score}/100</span></h3>
            """

            if details["issues"]:
                html_content += "<ul class='issues'>"
                for issue in details["issues"]:
                    html_content += f"<li>{issue}</li>"
                html_content += "</ul>"
            else:
                html_content += "<p>✅ No issues found</p>"

            html_content += "</div>"

        # Add AI recommendations if available
        if ai_recommendations:
            html_content += f"""
                <h2>AI-Powered Recommendations</h2>
                <div class="ai-recommendations">
                    {ai_recommendations}
                </div>
            """

        html_content += """
            </div>
        </body>
        </html>
        """

        # Attach HTML and image parts to email
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # Attach chart image
        img_part = MIMEImage(img_data)
        img_part.add_header(
            "Content-Disposition", f"attachment; filename={chart_filename}"
        )
        img_part.add_header("Content-ID", "<chart>")
        msg.attach(img_part)

        # Connect to SMTP server and send email
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        return True, "Email sent successfully!"

    except Exception as e:
        return False, f"Error sending email: {str(e)}"


# URL input
with st.form(key="url_form"):
    url_input = st.text_input(
        "Enter a URL to check (include https://)", "https://example.com"
    )

    # Submit button (pressing Enter will also trigger this)
    submit_button = st.form_submit_button(label="Analyze Accessibility")

    if submit_button:
        if url_input:
            with st.spinner(f"Analyzing {url_input}..."):
                try:
                    # Parse URL to display the domain
                    domain = urlparse(url_input).netloc

                    # Run analysis
                    results, checker = analyze_accessibility(url_input)

                    # Store results in session state
                    st.session_state.analysis_results = results
                    st.session_state.domain = domain
                    st.session_state.checker = checker

                except ConnectionError:
                    st.error(
                        f"Could not connect to {url_input}. Please check if the URL is correct and the website is accessible."
                    )
                except TimeoutError:
                    st.error(
                        f"Connection to {url_input} timed out. The server might be slow or unreachable."
                    )
                except ValueError as e:
                    st.error(f"Invalid URL format: {str(e)}")
                except Exception as e:
                    if "getaddrinfo failed" in str(e):
                        st.error(
                            f"Could not resolve host: {domain}. Please check if the URL is correct."
                        )
                    elif "certificate verify failed" in str(e):
                        st.error(
                            f"SSL certificate verification failed for {url_input}. The website might have security issues."
                        )
                    elif "Connection refused" in str(e):
                        st.error(
                            f"Connection refused by {domain}. The server might be blocking automated requests."
                        )
                    else:
                        st.error(f"Error analyzing URL: {str(e)}")
        else:
            st.warning("Please enter a URL to analyze")

# Display results if available in session state
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    domain = st.session_state.domain
    checker = st.session_state.checker

    # Display results in a structured manner
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader(f"Analysis Results for {domain}")

        # Overall score with colored styling
        score = results["total_score"]
        rating = checker.get_score_rating(score)
        score_class = get_score_class(score)

        st.markdown(
            f"""
        <div class='score-container'>
            <h2 class='{score_class}'>Overall Score: {score}/100 - {rating}</h2>
            <div style="background-color: #e9ecef; height: 30px; border-radius: 5px; margin-top: 10px;">
                <div style="background-color: {'#28a745' if score >= 90 else '#17a2b8' if score >= 80 else '#ffc107' if score >= 70 else '#fd7e14' if score >= 50 else '#dc3545'}; 
                     width: {score}%; height: 30px; border-radius: 5px; text-align: center; line-height: 30px; color: white;">
                    {score}%
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Category scores
        st.markdown("### Category Scores")

        for category, details in results["categories"].items():
            cat_score = int(details["score"] * 100)
            cat_class = get_score_class(cat_score)

            st.markdown(
                f"""
            <div class='category-header'>{category.title()}: <span class='{cat_class}'>{cat_score}/100</span></div>
            """,
                unsafe_allow_html=True,
            )

            st.progress(cat_score / 100)

            if details["issues"]:
                with st.expander(f"View {len(details['issues'])} issues"):
                    for issue in details["issues"]:
                        st.markdown(f"- {issue}")
            else:
                st.markdown("✅ No issues found")

    with col2:
        st.subheader("Accessibility Score Chart")

        # Generate chart
        fig = checker.visualize_results(results)
        st.pyplot(fig)

        # Download options
        st.markdown("### Download Results")

        # Create CSV of issues
        issues_data = []
        for category, details in results["categories"].items():
            for issue in details["issues"]:
                issues_data.append({"Category": category.title(), "Issue": issue})

        if issues_data:
            issues_df = pd.DataFrame(issues_data)
            csv = issues_df.to_csv(index=False)
            current_timestamp = int(time.time())  # Get current timestamp in seconds
            st.download_button(
                label="Download Issues as CSV",
                data=csv,
                file_name=f"accessibility_issues_{domain}_{current_timestamp}.csv",
                mime="text/csv",
            )

        # Download chart image
        img_str = fig_to_base64(fig)
        current_timestamp = int(time.time())  # Get current timestamp in seconds
        st.download_button(
            label="Download Chart as PNG",
            data=base64.b64decode(img_str),
            file_name=f"accessibility_chart_{domain}_{current_timestamp}.png",
            mime="image/png",
        )

    # After displaying the analysis results, add AI recommendations section
    st.markdown("---")
    st.subheader("AI-Powered Accessibility Recommendations")

    if st.session_state.ai_recommendations is None:
        if st.button("Generate AI Recommendations", key="generate_ai_main"):
            with st.spinner("Generating AI recommendations..."):
                recommendations = get_ai_recommendations(results)
                st.session_state.ai_recommendations = recommendations

    if st.session_state.ai_recommendations:
        st.markdown(st.session_state.ai_recommendations)
        if st.button("Generate New Recommendations", key="regenerate_ai_main"):
            with st.spinner("Generating new AI recommendations..."):
                recommendations = get_ai_recommendations(results)
                st.session_state.ai_recommendations = recommendations

    # Email report section
    st.markdown("---")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Email Report")
        recipient_email = st.text_input("Send report to email:", key="email_recipient")

        if st.button("Send Report via Email", key="send_email_report"):
            if recipient_email and "@" in recipient_email:
                with st.spinner("Sending email..."):
                    success, message = send_email_report(
                        recipient_email,
                        domain,
                        results,
                        st.session_state.ai_recommendations,
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.error("Please enter a valid email address")

    with col2:
        st.subheader("Email Options")
        st.info(
            "The report will include the accessibility scores, issues found, and AI recommendations (if generated)."
        )
        st.warning(
            "Make sure to check your spam folder if you don't receive the email within a few minutes."
        )

    # Reset recommendations if analyzing a new URL
    if submit_button and url_input:
        st.session_state.ai_recommendations = None

# Add footer with information
st.markdown(
    """---
### About Web4All Accessibility Checker
This tool checks websites against common accessibility guidelines including:
- Image alt text
- Heading structure
- Link descriptions
- Form labels
- Semantic HTML structure
- Color contrast (basic check)

The AI-powered recommendations feature uses OpenAI's API to provide tailored suggestions for improving accessibility.

For a comprehensive accessibility audit, consider using specialized tools and manual testing.
"""
)
