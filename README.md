# Web4All Accessibility Checker

![Web4All Logo](https://img.shields.io/badge/Web4All-Accessibility-blue)

A comprehensive tool for analyzing website accessibility compliance against common web accessibility guidelines (WCAG). Web4All helps developers and content creators identify and fix accessibility issues to build more inclusive web experiences.

## 📋 Table of Contents

- [Features](#-features)
- [Why Web Accessibility Matters](#-why-web-accessibility-matters)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Environment Setup](#-environment-setup)
- [Usage](#-usage)
  - [Web Interface](#web-interface-recommended)
  - [Command Line Interface](#command-line-interface)
- [Accessibility Criteria](#-accessibility-criteria)
- [AI-Powered Recommendations](#-ai-powered-recommendations)
- [Email Reports](#-email-reports)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)

## ✨ Features

- **Comprehensive Analysis**: Scans websites for common accessibility issues across multiple categories
- **Scoring System**: Provides an overall accessibility score and category-specific scores on a scale of 0-100
- **Visual Reports**: Generates radar charts and visualizations of accessibility scores
- **Detailed Issue Tracking**: Lists specific accessibility issues found on each page with suggestions for fixing
- **AI-Powered Recommendations**: Uses OpenAI's API to generate tailored recommendations for accessibility improvements
- **Email Reports**: Send accessibility reports directly to stakeholders via email
- **Interactive UI**: User-friendly Streamlit interface for ease of use
- **Exportable Reports**: Download results as CSV or charts as PNG images
- **Responsive Design**: Works across desktop and mobile devices

## 🌟 Why Web Accessibility Matters

Web accessibility ensures that websites and web applications are designed and developed so that people with disabilities can use them. According to the World Health Organization, over a billion people worldwide live with some form of disability. Implementing accessibility best practices benefits:

- People with visual, auditory, motor, or cognitive disabilities
- Elderly users with changing abilities
- Users with temporary disabilities (e.g., broken arm)
- Users with situational limitations (e.g., bright sunlight, noisy environments)

Beyond inclusion, web accessibility often:

- Improves SEO performance
- Reduces legal risks
- Enhances overall user experience for everyone

## 📁 Project Structure

```
web4all/
├── .env                    # Environment variables (API keys, SMTP settings)
├── .gitignore              # Git ignore file
├── .streamlit/             # Streamlit configuration folder
│   └── config.toml         # Streamlit configuration
├── app.py                  # Main Streamlit web application
├── main.py                 # Core accessibility checker functionality
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

## 📥 Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/arpankumarde/web4all
   cd web4all
   ```

2. Create a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Environment Setup

Create a `.env` file in the project root with the following variables:

```
# OpenAI API for AI recommendations
OPENAI_API_KEY=your_openai_api_key_here

# Email configuration for reports
AWS_SES_SMTP_EMAIL=your_email@example.com
AWS_SES_SMTP_HOST=your-smtp-server.com
AWS_SES_SMTP_PORT=465
AWS_SES_SMTP_USER=your_smtp_username
AWS_SES_SMTP_PASS=your_smtp_password
```

## 🚀 Usage

### Web Interface (Recommended)

Run the Streamlit web application:

```bash
streamlit run app.py
```

This will open a browser window with the user-friendly interface where you can:

1. Enter a URL to analyze
2. View the accessibility score breakdown
3. See detailed issues by category
4. Generate AI-powered recommendations
5. Download reports in CSV format or charts as PNG
6. Email reports to stakeholders

### Command Line Interface

You can also run a simplified version of the tool from the command line:

```bash
python main.py
```

Follow the prompts to enter a URL for analysis. This will display basic results in the terminal and show a visualization if you have a graphical environment.

## 🔍 Accessibility Criteria

Web4All checks websites against these key accessibility categories:

| Category      | Weight | Description                       | Tests Performed                       |
| ------------- | ------ | --------------------------------- | ------------------------------------- |
| **Images**    | 15%    | Checks images for proper alt text | Alt text presence and quality         |
| **Headings**  | 15%    | Analyzes heading structure        | H1 usage, heading hierarchy           |
| **Links**     | 10%    | Evaluates link text quality       | Descriptive links, skip links         |
| **Forms**     | 15%    | Reviews form accessibility        | Form labels, form error handling      |
| **Structure** | 20%    | Examines semantic HTML structure  | Semantic elements, landmarks          |
| **Contrast**  | 15%    | Basic color contrast assessment   | Text-background contrast ratio        |
| **Keyboard**  | 10%    | Evaluates keyboard accessibility  | Focus indicators, keyboard navigation |

The tool assigns a weighted score to each category and calculates an overall accessibility score on a scale of 0-100.

## 🤖 AI-Powered Recommendations

Web4All integrates with OpenAI's API to generate tailored recommendations for improving website accessibility based on the specific issues detected. These recommendations:

- Prioritize the most critical accessibility barriers
- Provide practical, actionable suggestions
- Include code examples where relevant
- Explain the rationale behind each recommendation

To use this feature, ensure you have set your `OPENAI_API_KEY` in the `.env` file or enter it when prompted.

## 📧 Email Reports

You can send comprehensive accessibility reports to stakeholders directly from the application. Email reports include:

- Overall accessibility score
- Category breakdown scores
- Visual chart representation
- List of detected issues
- AI-powered recommendations (if generated)

To use this feature, configure the SMTP settings in your `.env` file.

## 🔮 Future Improvements

- Add ARIA attribute validation
- Implement mobile accessibility checks
- Include automated remediation suggestions
- Support batch URL processing
- Add historical tracking of accessibility scores
- Integrate with CI/CD pipelines

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
