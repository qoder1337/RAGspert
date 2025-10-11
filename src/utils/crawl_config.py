from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def get_browser_conf():
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )

    return browser_config


def get_md_conf():
    prune_filter = PruningContentFilter(
        threshold=0.6,
        threshold_type="dynamic",
        # min_word_threshold=10,
    )

    md_generator = DefaultMarkdownGenerator(
        content_filter=prune_filter,
        # options={
        #     "ignore_images": True,
        #     "ignore_links": True,
        #     "skip_internal_links": True,
        #     # "escape_html": False,
        # },
    )
    return md_generator


def get_crawl_conf():
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=get_md_conf(),
        excluded_tags=["form", "header", "footer", "nav"],
        word_count_threshold=20,  # Minimum words per block
        # excluded_selector="div#BorlabsCookieBox, div.lesson__disclaimer, p.cta__heading, div#cookie-banner, div.et_pb_row_2, div.ld-focus-sidebar, div#cmplz-cookiebanner-container",
        # remove_overlay_elements=True,
        # magic=True,
        # keep_data_attributes=False,
        # only_text=True,
    )
    return crawl_config
