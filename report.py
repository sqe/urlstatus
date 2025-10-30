import csv
import json

def split_by_status(status_dict):
    http200 = []
    non200 = []
    for uri, status in status_dict.items():
        if status == 200:
            http200.append({"uri": uri, "status": status})
        # Exclude redirects (status 300-399)
        elif not (isinstance(status, int) and 300 <= status < 400):
            non200.append({"uri": uri, "status": status})
    return http200, non200

def write_csv(records, path):
    with open(path, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["uri", "status"])
        writer.writeheader()
        writer.writerows(records)

def write_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

def report_output(http200, non200, output_format, outprefix, click_echo):
    if output_format == "csv":
        csv_200 = f"{outprefix}_http200.csv"
        csv_non200 = f"{outprefix}_http_non200.csv"
        write_csv(http200, csv_200)
        write_csv(non200, csv_non200)
        click_echo(f"HTTP 200 CSV: {csv_200}", fg="green")
        click_echo(f"HTTP non-200 CSV: {csv_non200}", fg="green")
    elif output_format == "json":
        json_200 = f"{outprefix}_http200.json"
        json_non200 = f"{outprefix}_http_non200.json"
        write_json(http200, json_200)
        write_json(non200, json_non200)
        click_echo(f"HTTP 200 JSON: {json_200}", fg="green")
        click_echo(f"HTTP non-200 JSON: {json_non200}", fg="green")
    else:
        click_echo("Unknown output format", fg="red")
