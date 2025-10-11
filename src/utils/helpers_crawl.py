import re
from urllib.parse import urlparse

code_line_pattern = re.compile(r"^\s*\d+\s*$")


def clean_codeblocks(text):
    return "\n".join(
        line for line in text.split("\n") if not code_line_pattern.match(line)
    )


def remove_md_links(text):
    filtered_text = re.sub(r"\(https?://[^)]*\)", "", text)
    return filtered_text.strip()


def extract_domain(url: str) -> str:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    domain_parts = domain.split(".")

    if len(domain_parts) >= 3:
        return "-".join(domain_parts[-2:])

    return "-".join(domain_parts)
