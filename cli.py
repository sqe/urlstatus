import click
import asyncio
from config import get_config
from crawl import crawl_site
from report import split_by_status, report_output

@click.command()
@click.option("--target-url", help="Target website to crawl", required=True)
@click.option("--max-concurrent", default=10, type=int, show_default=True, help="Max concurrent requests")
@click.option("--output-format", type=click.Choice(['csv', 'json']), default='csv', show_default=True, help="Result file format (csv or json)")
@click.option("--output-prefix", default="crawler_report", show_default=True, help="Prefix for output files")
def run(target_url, max_concurrent, output_format, output_prefix):
    cli_args = {
        "target_url": target_url,
        "max_concurrent": max_concurrent
    }
    config = get_config(cli_args)
    click.secho(f"Website Target: {config['target_url']}", fg="yellow", bold=True)
    loop = asyncio.get_event_loop()
    status_dict, link_graph = loop.run_until_complete(crawl_site(config, click.secho))
    http200, non200 = split_by_status(status_dict)
    # Write .csv/.json as requested
    report_output(http200, non200, output_format, output_prefix, click.secho)
    click.secho("Done.", fg="magenta", bold=True)

if __name__ == "__main__":
    run()
