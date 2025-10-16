import asyncio
from xml.etree import ElementTree
from urllib.parse import urljoin, urlparse
from curl_cffi.requests import AsyncSession
from crawl4ai import AsyncWebCrawler
from src.utils.process_doc import process_and_store_document
from src.utils.helpers_crawl import clean_codeblocks, remove_md_links
from src.utils.crawl_config import get_browser_conf, get_crawl_conf
from src.utils.crawl_status import crawl_status


async def process_url(
    url: str,
    crawler: AsyncWebCrawler,
    semaphore: asyncio.Semaphore = None,
    i: int = None,
    source_name: str = None,
):
    crawl_config = get_crawl_conf()

    try:
        if semaphore:
            async with semaphore:
                result = await crawler.arun(
                    url=url,
                    config=crawl_config,
                    # session_id="session1"
                )
        else:
            result = await crawler.arun(url=url, config=crawl_config)

        if result.success:
            print(f"Successfully crawled: {url}")
            fit_md = clean_codeblocks(result.markdown.fit_markdown)
            fit_md = remove_md_links(fit_md)
            print(fit_md)

            ### PROCESS, VECTORIZE UND SAVE TO DB with source_name
            # await process_and_store_document(
            #     url=url, markdown=fit_md, source_name=source_name
            # )

            # ✅ Update Status
            crawl_status.update(source_name, success=True)

        else:
            print(f"Failed: {url} - Error: {result.error_message}")
            crawl_status.update(source_name, success=False)

    except Exception as e:
        print(f"Error processing URL {url}: {e}")


async def crawl_parallel(
    urls: list[str], max_concurrent: int = 3, source_name: str = None
):
    """
    Crawl multiple URLs in parallel with a concurrency limit.
    session_id="session1" noch ändern

    Args:
        urls (list[str]): _description_
        max_concurrent (int, optional): _description_. Defaults to 3.
    """

    browser_config = get_browser_conf()

    crawler = AsyncWebCrawler(config=browser_config)

    await crawler.start()
    semaphore = asyncio.Semaphore(max_concurrent)

    try:
        # Process all URLs in parallel with limited concurrency
        await asyncio.gather(
            *[
                process_url(
                    url=url,
                    crawler=crawler,
                    semaphore=semaphore,
                    i=i,
                    source_name=source_name,
                )
                for i, url in enumerate(urls)
            ]
        )

    finally:
        await crawler.close()


async def get_urls_from_xml(sitemap_url: str = "https://ai.pydantic.dev/sitemap.xml"):
    """
    Fetches all URLs from the Pydantic AI documentation.
    Uses the sitemap (.../sitemap.xml) to get these URLs.

    Returns:
        List[str]: List of URLs
    """
    try:
        async with AsyncSession() as s:
            response = await s.get(sitemap_url, timeout=30)
            response.raise_for_status()

        # Parse the XML
        root = ElementTree.fromstring(response.content)

        # Extract all URLs from the sitemap
        # The namespace is usually defined in the root element
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        ### CHECK for sitemap-index
        sitemap_locs = root.findall(".//ns:sitemap/ns:loc", namespace)

        if sitemap_locs:
            print(f"📂 Sitemap-Index found with {len(sitemap_locs)} Sub-Sitemaps")
            all_urls = []

            for sitemap_loc in sitemap_locs:
                sub_sitemap_url = sitemap_loc.text
                print(f"  📄 Sub-Sitemap: {sub_sitemap_url}")
                sub_urls = await get_urls_from_xml(sub_sitemap_url)
                all_urls.extend(sub_urls)

            return all_urls

        urls = [loc.text for loc in root.findall(".//ns:loc", namespace)]

        return urls

    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []


async def run_crawl(
    url_input: str | list[str] = None,
    max_concurrent: int = None,
    blocklist: list[str] = None,
    source_name: str = None,
):
    if isinstance(url_input, list):
        if blocklist is not None:
            url_input = [
                url
                for url in url_input
                if not any(word in url.lower() for word in blocklist)
            ]
            print(f"cleaned by blocklist. New Listlength: {len(url_input)} Elements")
        result = (
            await crawl_parallel(
                urls=url_input, max_concurrent=max_concurrent, source_name=source_name
            )
            if max_concurrent is not None
            else await crawl_parallel(urls=url_input, source_name=source_name)
        )
        return result

    else:
        if blocklist is not None:
            if any(word in url_input.lower() for word in blocklist):
                return "URL IN BLOCKLIST"
        browser_config = get_browser_conf()
        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.start()
        try:
            return await process_url(
                url=url_input, crawler=crawler, source_name=source_name
            )
        finally:
            await crawler.close()


async def find_sitemap(base_url: str) -> str | None:
    """
    automatic Sitemap finder

    looks for:
    1. /sitemap.xml
    2. /sitemap_index.xml
    3. robots.txt nach Sitemap-Eintrag

    Args:
        base_url: i.e. "https://ai.pydantic.dev"

    Returns:
        Sitemap URL or None
    """
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    # Standard-Sitemap-Locations
    common_paths = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap-index.xml",
        "/sitemaps/sitemap.xml",
        "/sitemap/sitemap.xml",
    ]

    async with AsyncSession() as session:
        for path in common_paths:
            url = urljoin(domain, path)
            try:
                response = await session.get(url, timeout=10)
                if response.status_code == 200 and "xml" in response.headers.get(
                    "content-type", ""
                ):
                    print(f"✅ Sitemap found: {url}")
                    return url
            except Exception as e:
                print(e)
                continue

        try:
            robots_url = urljoin(domain, "/robots.txt")
            response = await session.get(robots_url, timeout=10)

            if response.status_code == 200:
                for line in response.text.split("\n"):
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        print(f"✅ Sitemap found in robots.txt: {sitemap_url}")
                        return sitemap_url
        except Exception as e:
            print(e)
            pass

    print(f"❌ no Sitemap found for {domain}")
    return None


async def init_crawling(
    url_or_sitemap: str,
    max_concurrent: int = 3,
    blocklist: list[str] = None,
    source_name: str = None,
):
    """
    Main-Function: Start of Crawling

    Args:
        url_or_sitemap:
            - Base-URL ("https://ai.pydantic.dev")
            - Direct Sitemap-URL ("https://ai.pydantic.dev/sitemap.xml")
            - single Site-URL
        max_concurrent: Anzahl paralleler Requests
        blocklist: Liste von Wörtern zum Filtern

    Examples:
        >>> await init_crawling("https://ai.pydantic.dev")
        >>> await init_crawling("https://ai.pydantic.dev/sitemap.xml")
        >>> await init_crawling("https://docs.python.org", blocklist=["tutorial"])
    """
    if not source_name:
        print("⚠️ Warning: No source_name provided. Using URL as fallback.")
        source_name = urlparse(url_or_sitemap).netloc

    if "sitemap" in url_or_sitemap.lower() and url_or_sitemap.endswith(".xml"):
        print(f"🗺️ Sitemap found: {url_or_sitemap}")
        sitemap_url = url_or_sitemap
    else:
        print(f"🔍 Scanning for Sitemap für: {url_or_sitemap}")
        sitemap_url = await find_sitemap(url_or_sitemap)

        if not sitemap_url:
            print("no Sitemap gefunden.")
            return

    urls = await get_urls_from_xml(sitemap_url)

    if not urls:
        print("❌ No URLs in Sitemap found")
        return

    print(f"📋 found {len(urls)} URLs for Crawling")

    # ✅ Register Crawl Job
    crawl_status.start(source_name, total_urls=len(urls))

    try:
        await run_crawl(
            url_input=urls,
            max_concurrent=max_concurrent,
            blocklist=blocklist,
            source_name=source_name,
        )

        # ✅ Mark as finished
        crawl_status.finish(source_name)
        print(f"✅ Crawling completed for '{source_name}'")

    except Exception as e:
        print(f"❌ Crawling failed: {e}")
        crawl_status.finish(source_name)
