import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from urllib.parse import urlparse
import re

# import matplotlib
# matplotlib.use("Agg")


class WebAccessibilityChecker:
    def __init__(self):
        self.results = {}
        self.issues = []
        self.total_score = 0
        self.categories = {
            "images": {"weight": 0.15, "score": 0, "tests": ["alt_text"]},
            "headings": {"weight": 0.15, "score": 0, "tests": ["heading_structure"]},
            "links": {
                "weight": 0.10,
                "score": 0,
                "tests": ["descriptive_links", "skip_links"],
            },
            "forms": {
                "weight": 0.15,
                "score": 0,
                "tests": ["form_labels", "form_errors"],
            },
            "contrast": {"weight": 0.15, "score": 0, "tests": ["color_contrast"]},
            "keyboard": {"weight": 0.10, "score": 0, "tests": ["keyboard_access"]},
            "structure": {
                "weight": 0.20,
                "score": 0,
                "tests": ["semantic_structure", "landmarks"],
            },
        }

    def fetch_url(self, url):
        """Fetch the content of the URL and parse it with BeautifulSoup"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    def check_alt_text(self, soup):
        """Check if all images have alt text"""
        images = soup.find_all("img")
        total_images = len(images)
        if total_images == 0:
            # No images to check
            return 1.0, []

        missing_alt = 0
        empty_alt = 0
        issues = []

        for img in images:
            if not img.has_attr("alt"):
                missing_alt += 1
                issues.append(
                    f"Image missing alt attribute: {img.get('src', 'unknown')}"
                )
            elif img["alt"].strip() == "" and not img.get("role") == "presentation":
                empty_alt += 1
                issues.append(f"Image has empty alt text: {img.get('src', 'unknown')}")

        score = 1.0 - ((missing_alt + empty_alt * 0.5) / total_images)
        return max(0, min(score, 1.0)), issues

    def check_heading_structure(self, soup):
        """Check heading structure (h1, h2, etc)"""
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not headings:
            return 0.0, ["No headings found on page"]

        issues = []
        h1_count = len(soup.find_all("h1"))

        if h1_count == 0:
            issues.append("No H1 heading found")
        elif h1_count > 1:
            issues.append(f"Multiple H1 headings found ({h1_count})")

        # Check for heading level skips
        levels = [int(h.name[1]) for h in headings]
        prev_level = 0
        skips = 0
        for level in levels:
            if level > prev_level + 1 and prev_level > 0:
                skips += 1
                issues.append(f"Heading level skip from h{prev_level} to h{level}")
            prev_level = level

        # Calculate score based on H1 presence and heading skips
        score = 1.0
        if h1_count == 0:
            score -= 0.5
        elif h1_count > 1:
            score -= 0.3

        if skips > 0:
            score -= min(0.5, skips * 0.1)  # Penalize for skips, max penalty 0.5

        return max(0, score), issues

    def check_descriptive_links(self, soup):
        """Check for descriptive link texts"""
        links = soup.find_all("a")
        if not links:
            return 1.0, []

        total_links = len(links)
        poor_links = 0
        issues = []

        poor_link_texts = [
            "click here",
            "read more",
            "more",
            "link",
            "here",
            "this",
            "page",
        ]

        for link in links:
            link_text = link.get_text().strip().lower()

            # Skip links with images that might have alt text
            if link.find("img") and not link_text:
                continue

            if not link_text:
                poor_links += 1
                issues.append(f"Empty link text: {link.get('href', 'unknown')}")
            elif link_text in poor_link_texts or len(link_text) < 3:
                poor_links += 1
                issues.append(
                    f"Non-descriptive link text: '{link_text}' for {link.get('href', 'unknown')}"
                )

        score = 1.0 - (poor_links / total_links)
        return max(0, score), issues

    def check_form_labels(self, soup):
        """Check if form controls have associated labels"""
        inputs = soup.find_all(["input", "select", "textarea"])
        if not inputs:
            return 1.0, []  # No form elements

        total_inputs = 0
        unlabeled = 0
        issues = []

        # Exclude hidden, submit, button, and image inputs
        excluded_types = ["hidden", "submit", "button", "image"]

        for inp in inputs:
            if inp.name == "input" and inp.get("type") in excluded_types:
                continue

            total_inputs += 1
            has_label = False

            # Check for id attribute and matching label
            if inp.has_attr("id"):
                label = soup.find("label", attrs={"for": inp["id"]})
                if label:
                    has_label = True

            # Check if input is wrapped in a label
            parent_labels = [p for p in inp.parents if p.name == "label"]
            if parent_labels:
                has_label = True

            # Check aria-label
            if inp.has_attr("aria-label") and inp["aria-label"].strip():
                has_label = True

            if not has_label:
                unlabeled += 1
                issues.append(
                    f"Form control missing label: {inp.get('name', 'unnamed')} {inp.get('type', '')}"
                )

        if total_inputs == 0:
            return 1.0, []

        score = 1.0 - (unlabeled / total_inputs)
        return max(0, score), issues

    def check_semantic_structure(self, soup):
        """Check for semantic HTML structure"""
        semantics = soup.find_all(
            ["header", "footer", "nav", "main", "article", "section", "aside"]
        )
        landmarks = len(semantics)

        score = min(1.0, landmarks / 3)  # Expect at least 3 semantic elements

        issues = []
        if landmarks == 0:
            issues.append("No semantic HTML elements found")

        # Check if page has main tag
        if not soup.find("main"):
            issues.append("No <main> element found")
            score -= 0.3

        return max(0, score), issues

    def check_color_contrast(self, soup):
        """Simple check for potential color contrast issues based on inline styles"""
        # This is a simplified version that only checks inline styles
        elements_with_color = soup.select('[style*="color"]')
        potential_issues = 0
        issues = []

        for element in elements_with_color:
            style = element.get("style", "")

            # Look for very light colors against white or very dark colors against black
            if re.search(r"color:\s*#[ef][ef][ef]|color:\s*rgb\(2[3-5]\d", style):
                potential_issues += 1
                issues.append("Potential low contrast light text")

            if re.search(r"color:\s*#[0-2][0-2][0-2]|color:\s*rgb\([0-2]\d", style):
                potential_issues += 1
                issues.append("Potential low contrast dark text")

        # Simple heuristic - more accurate testing would require rendering and visual analysis
        score = 1.0 - min(0.5, potential_issues * 0.1)

        if not issues:
            issues.append("Limited contrast check performed (inline styles only)")

        return score, issues

    def run_accessibility_check(self, url):
        """Run all accessibility checks and calculate overall score"""
        soup = self.fetch_url(url)
        if not soup:
            return {
                "url": url,
                "total_score": 0,
                "categories": {},
                "issues": ["Failed to fetch URL"],
            }

        # Store results
        results = {"url": url, "categories": {}}
        all_issues = []

        # Check images
        alt_score, alt_issues = self.check_alt_text(soup)
        results["categories"]["images"] = {"score": alt_score, "issues": alt_issues}
        all_issues.extend(alt_issues)

        # Check headings
        headings_score, headings_issues = self.check_heading_structure(soup)
        results["categories"]["headings"] = {
            "score": headings_score,
            "issues": headings_issues,
        }
        all_issues.extend(headings_issues)

        # Check links
        links_score, links_issues = self.check_descriptive_links(soup)
        results["categories"]["links"] = {"score": links_score, "issues": links_issues}
        all_issues.extend(links_issues)

        # Check forms
        forms_score, forms_issues = self.check_form_labels(soup)
        results["categories"]["forms"] = {"score": forms_score, "issues": forms_issues}
        all_issues.extend(forms_issues)

        # Check semantic structure
        structure_score, structure_issues = self.check_semantic_structure(soup)
        results["categories"]["structure"] = {
            "score": structure_score,
            "issues": structure_issues,
        }
        all_issues.extend(structure_issues)

        # Check color contrast
        contrast_score, contrast_issues = self.check_color_contrast(soup)
        results["categories"]["contrast"] = {
            "score": contrast_score,
            "issues": contrast_issues,
        }
        all_issues.extend(contrast_issues)

        # Calculate weighted score
        category_weights = {
            "images": 0.15,
            "headings": 0.15,
            "links": 0.10,
            "forms": 0.15,
            "structure": 0.20,
            "contrast": 0.15,
        }

        total_score = 0
        total_weight = 0

        for category, details in results["categories"].items():
            if category in category_weights:
                total_score += details["score"] * category_weights[category]
                total_weight += category_weights[category]

        # Normalize score to account for categories that couldn't be tested
        normalized_score = total_score / total_weight if total_weight > 0 else 0
        results["total_score"] = round(normalized_score * 100)
        results["issues"] = all_issues

        return results

    def get_score_rating(self, score):
        """Convert numerical score to a rating"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 50:
            return "Poor"
        else:
            return "Very Poor"

    def format_results(self, results):
        """Format the results for display"""
        score = results["total_score"]
        rating = self.get_score_rating(score)

        output = f"## Accessibility Report for {results['url']}\n\n"
        output += f"### Overall Score: {score}/100 - {rating}\n\n"

        output += "### Category Scores:\n\n"
        for category, details in results["categories"].items():
            cat_score = int(details["score"] * 100)
            output += f"- **{category.title()}**: {cat_score}/100\n"

        output += "\n### Top Issues:\n\n"
        for i, issue in enumerate(results["issues"][:10]):  # Show top 10 issues
            output += f"{i+1}. {issue}\n"

        if len(results["issues"]) > 10:
            output += f"\n...and {len(results['issues']) - 10} more issues.\n"

        return output

    def visualize_results(self, results):
        """Create a radar chart of category scores"""
        categories = []
        scores = []

        for category, details in results["categories"].items():
            categories.append(category.title())
            scores.append(details["score"] * 100)

        # Create radar chart
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

        # Number of categories
        N = len(categories)
        angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
        angles += angles[:1]  # Close the loop

        # Add scores
        scores += scores[:1]  # Close the loop

        # Draw the chart
        ax.plot(angles, scores, linewidth=1, linestyle="solid")
        ax.fill(angles, scores, alpha=0.1)

        # Add category labels
        plt.xticks(angles[:-1], categories)

        # Add score labels (0-100)
        plt.yticks([20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="grey")
        plt.ylim(0, 100)

        # Add title
        plt.title(
            f'Accessibility Score: {results["total_score"]}/100 - {self.get_score_rating(results["total_score"])}',
            size=15,
        )

        return fig


# Create a function to analyze a URL
def analyze_accessibility(url):
    checker = WebAccessibilityChecker()
    results = checker.run_accessibility_check(url)
    return results, checker


# Command-line interface
if __name__ == "__main__":
    url = input("Enter a URL to check (include https://): ")
    results, checker = analyze_accessibility(url)
    formatted_results = checker.format_results(results)
    print(formatted_results)

    # Generate and display chart
    fig = checker.visualize_results(results)
    plt.show()
