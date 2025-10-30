#!/usr/bin/env python3
import asyncio
import aiohttp
import re
import csv
from urllib.parse import urljoin, urlparse
import networkx as nx

TARGET_URL = "https://nebius.com/"
DOMAIN = urlparse(TARGET_URL).netloc
MAX_CONCURRENT = 10

async def get_links_from_html(html, base_url, visited):
    links = set()
    for match in re.findall(r'<a\s[^>]*href=["\'](.*?)["\']', html, re.IGNORECASE):
        href = match.strip()
        full_url = urljoin(base_url, href.split('#')[0])
        parsed = urlparse(full_url)
        if parsed.netloc == DOMAIN and full_url not in visited:
            links.add(full_url)
    print(f"[DEBUG] Found {len(links)} internal links on {base_url}")
    return list(links)

async def fetch(session, url, visited):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            status = response.status
            print(f"[DEBUG] Fetched {url} - HTTP {status}")
            if status != 200:
                print(f"[WARN] Skipped {url}, status {status}")
                return url, status, []
            html = await response.text()
            links = await get_links_from_html(html, url, visited)
            return url, status, links
    except Exception as e:
        print(f"[ERROR] Error accessing {url}: {e}")
        return url, f"Error: {e}", []

async def crawl_site(start_url):
    visited = set()
    to_visit = set([start_url])
    status_dict = {}
    link_graph = nx.DiGraph()
    print("[INFO] Starting async crawl at", start_url)
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    async with aiohttp.ClientSession() as session:
        async def worker(url):
            async with sem:
                if url in visited:
                    print(f"[DEBUG] Already visited {url}, skip.")
                    return []
                visited.add(url)
                url, status, links = await fetch(session, url, visited)
                status_dict[url] = status
                link_graph.add_node(url)
                for link in links:
                    link_graph.add_edge(url, link)
                return links
        queue = set([start_url])
        while queue:
            tasks = [worker(url) for url in queue]
            queue.clear()
            results = await asyncio.gather(*tasks)
            for linklist in results:
                for link in linklist:
                    if link not in visited and link not in to_visit:
                        to_visit.add(link)
                        queue.add(link)
            print(f"[INFO] Progress: {len(visited)} visited, {len(queue)} in queue.")
    print("[INFO] Async crawl COMPLETE. Pages visited:", len(visited))
    return status_dict, link_graph

def markdown_status_table(status_dict):
    ok_rows, fail_rows = [], []
    for uri, status in status_dict.items():
        if status == 200:
            ok_rows.append((uri, status))
        else:
            fail_rows.append((uri, status))
    # Pad lists so each row has both columns
    max_len = max(len(ok_rows), len(fail_rows))
    ok_rows += [('', '')] * (max_len - len(ok_rows))
    fail_rows += [('', '')] * (max_len - len(fail_rows))
    lines = ["| HTTP 200 URI | Status | HTTP non-200 URI | Status |\n|--------------|--------|-------------------|--------|"]
    for i in range(max_len):
        ok_uri, ok_status = ok_rows[i]
        fail_uri, fail_status = fail_rows[i]
        lines.append(f"| [{ok_uri}]({ok_uri}) | {ok_status} | [{fail_uri}]({fail_uri}) | {fail_status} |")
    return "\n".join(lines)

def csv_status_table(status_dict):
    # Three columns: URI, Status, OK/Fail
    rows = [("URI", "Status", "Group")]
    for uri, status in status_dict.items():
        label = "HTTP 200" if status == 200 else "HTTP non-200"
        rows.append((uri, status, label))
    return rows

def markdown_graph(graph):
    text = "# Sitemap\n\n"
    roots = [TARGET_URL]
    def dfs(node, indent):
        text_lines = []
        text_lines.append(" " * indent + f"* [{node}]({node})")
        children = list(graph.successors(node))
        for child in children:
            text_lines.extend(dfs(child, indent + 2))
        return text_lines
    already = set()
    for root in roots:
        for line in dfs(root, 0):
            if line not in already:
                text += line + "\n"
                already.add(line)
    return text

if __name__ == "__main__":
    print("[INFO] Starting Nebius.com async sitemap crawl with debug output.")
    loop = asyncio.get_event_loop()
    status_dict, link_graph = loop.run_until_complete(crawl_site(TARGET_URL))

    # Write markdown status table
    table_md = markdown_status_table(status_dict)
    with open("crawler_report.md", "w", encoding="utf-8") as f:
        f.write(table_md)
    print("[INFO] Table written to crawler_report.md")

    # Write CSV file for results
    csv_rows = csv_status_table(status_dict)
    with open("crawler_report.csv", "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)
    print("[INFO] Table written to crawler_report.csv")

    # Write sitemap graph to sitemap_report.md
    md_sitemap = markdown_graph(link_graph)
    with open("sitemap_report.md", "w", encoding="utf-8") as f:
        f.write(md_sitemap)
    print("[INFO] Sitemap written to sitemap_report.md")
    print("[INFO] Process complete.")
