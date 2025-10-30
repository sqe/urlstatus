CONFIG_DEFAULTS = {
    "target_url": "https://nebius.com/",
    "max_concurrent": 10,
    "crawler_report_md": "crawler_report.md",
    "crawler_report_csv": "crawler_report.csv",
    "sitemap_report_md": "sitemap_report.md"
}
def get_config(cli_args):
    # Merge CLI args with defaults
    config = dict(CONFIG_DEFAULTS)
    config.update({k: v for k, v in cli_args.items() if v is not None})
    return config
