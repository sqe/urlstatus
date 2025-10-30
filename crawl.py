import asyncio, aiohttp, re, networkx
from urllib.parse import urljoin, urlparse

async def get_links_from_html(html, base_url, visited, domain):
    links = set()
    for match in re.findall(r'<a\s[^>]*href=["\'](.*?)["\']', html, re.IGNORECASE):
        href = match.strip()
        full_url = urljoin(base_url, href.split('#')[0])
        parsed = urlparse(full_url)
        if parsed.netloc == domain and full_url not in visited:
            links.add(full_url)
    return list(links)

async def fetch(session, url, visited, domain):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            status = response.status
            if status != 200:
                return url, status, []
            html = await response.text()
            links = await get_links_from_html(html, url, visited, domain)
            return url, status, links
    except Exception as e:
        return url, f"Error: {e}", []

async def crawl_site(config, click_echo):
    target_url = config["target_url"]
    domain = urlparse(target_url).netloc
    max_concurrent = config["max_concurrent"]
    visited, to_visit = set(), set([target_url])
    status_dict, link_graph = {}, networkx.DiGraph()
    sem = asyncio.Semaphore(max_concurrent)
    click_echo(f"[INFO] Beginning crawl: {target_url}", fg="green")
    async with aiohttp.ClientSession() as session:
        async def worker(url):
            async with sem:
                if url in visited:
                    return []
                visited.add(url)
                url, status, links = await fetch(session, url, visited, domain)
                status_dict[url] = status
                link_graph.add_node(url)
                for link in links:
                    link_graph.add_edge(url, link)
                return links
        queue = set([target_url])
        while queue:
            tasks = [worker(url) for url in queue]
            queue.clear()
            results = await asyncio.gather(*tasks)
            for linklist in results:
                for link in linklist:
                    if link not in visited and link not in to_visit:
                        to_visit.add(link)
                        queue.add(link)
            click_echo(f"[INFO] Progress: {len(visited)} visited, {len(queue)} queued.", fg="blue")
    click_echo(f"[INFO] Done. {len(visited)} pages visited.", fg="green")
    return status_dict, link_graph
