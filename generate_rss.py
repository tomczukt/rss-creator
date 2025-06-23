import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import shutil
import os

SOURCE_URL = "https://unknow.news/last"
FEED_FILENAME = "feed.xml"
MAX_ITEMS = 30

def extract_issue_date(soup):
    """Pobiera datę wydania z nagłówka typu [YYYY-MM-DD]"""
    date_tag = soup.find("b")
    if date_tag:
        raw_date = date_tag.get_text(strip=True)
        try:
            dt = datetime.strptime(raw_date.strip("[]"), "%Y-%m-%d")
            return dt
        except ValueError:
            pass
    return datetime.utcnow()

def fetch_entries_and_date():
    res = requests.get(SOURCE_URL)
    soup = BeautifulSoup(res.text, "html.parser")
    issue_date = extract_issue_date(soup)

    entries = []
    for li in soup.select("ol > li"):
        strong = li.find("strong")
        a = li.find("a", href=True)
        desc = li.find("span", id=lambda x: x and x.startswith("opis"))

        if not strong or not a:
            continue

        title = strong.get_text(strip=True)
        link = a["href"]
        description = desc.get_text(strip=True) if desc else ""
        pub_date = issue_date.strftime("%a, %d %b %Y %H:%M:%S +0000")

        entries.append({
            "title": title,
            "link": link,
            "description": description,
            "guid": link,
            "pubDate": pub_date
        })

    return entries, issue_date

def archive_previous_feed(issue_date):
    if os.path.exists(FEED_FILENAME):
        archive_name = f"feed_{issue_date.strftime('%Y%m%d')}.xml"
        shutil.copy(FEED_FILENAME, archive_name)

def write_rss(entries, issue_date):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "#unknowNews (nieoficjalny RSS)"
    ET.SubElement(channel, "link").text = SOURCE_URL
    ET.SubElement(channel, "description").text = "Najnowsze wpisy z newslettera unknow.news"
    ET.SubElement(channel, "pubDate").text = issue_date.strftime("%a, %d %b %Y %H:%M:%S +0000")

    for e in entries[:MAX_ITEMS]:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = e["title"]
        ET.SubElement(item, "link").text = e["link"]
        ET.SubElement(item, "description").text = e["description"]
        ET.SubElement(item, "guid").text = e["guid"]
        ET.SubElement(item, "pubDate").text = e["pubDate"]

    tree = ET.ElementTree(rss)
    tree.write(FEED_FILENAME, encoding="utf-8", xml_declaration=True)

def main():
    entries, issue_date = fetch_entries_and_date()
    archive_previous_feed(issue_date)
    write_rss(entries, issue_date)

if __name__ == "__main__":
    main()
