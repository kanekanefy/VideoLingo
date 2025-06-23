import requests
import csv

# 从 firecrawl 批次爬取结果的 API 端点（此 URL 由 firecrawl 返回）
EXTRACTION_URL = "https://api.firecrawl.dev/v1/batch/scrape/2b1b33d9-8a29-4443-ac46-bd152ff09fb3"
FIRECRAWL_API_TOKEN = "fc-ede6b46b501740feb65252f1a86dc168"

def fetch_extraction_results():
    headers = {"Authorization": f"Bearer {FIRECRAWL_API_TOKEN}"}
    response = requests.get(EXTRACTION_URL, headers=headers)
    response.raise_for_status()
    data = response.json()
    # 假设返回的数据格式为 { "results": [ { "name": ..., "url": ..., "description": ... }, ... ] }
    if "results" in data:
        return data["results"]
    # 若直接返回列表，则直接使用
    return data

def main():
    # 获取爬取结果，限制只保留 10 个
    results = fetch_extraction_results()
    if isinstance(results, dict):
        results = results.get("results", [])
    results = results[:10]
    # 将结果保存为 CSV 文件
    with open("companies.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "description"])
        writer.writeheader()
        for item in results:
            writer.writerow(item)
    print("CSV 文件已生成: companies.csv")

if __name__ == "__main__":
    main()
