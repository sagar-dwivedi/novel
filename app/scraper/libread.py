from urllib.parse import urljoin

from bs4 import BeautifulSoup
from slugify import slugify
from .base_scraper import BaseScraper, ChapterMetadata, NovelMetadata


class LibReadScraper(BaseScraper):
    async def scrape_metadata(self, url: str) -> NovelMetadata:
        print(f"🔍 Starting metadata scraping for URL: {url}")
        
        html = await self.fetch_html(url)
        print(f"📄 HTML fetched: {'Success' if html else 'Failed'}")
        
        if not html:
            raise ValueError(f"Failed to fetch HTML from {url}")

        soup = BeautifulSoup(html, "lxml")
        print("✅ HTML parsed with BeautifulSoup")

        # Extract title
        print("🔍 Looking for title...")
        title_elem = soup.find("div", class_="m-desc")
        if title_elem:
            title_elem = title_elem.find("h1", class_="tit")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        print(f"📖 Title found: {title}")

        # Extract author
        print("🔍 Looking for author...")
        author = "Unknown Author"
        author_elem = soup.find("span", class_="glyphicon-user")
        if author_elem:
            print("✅ Found author icon")
            author_parent = author_elem.find_parent("div", class_="item")
            if author_parent:
                author_link = author_parent.find("a", class_="a1")
                if author_link:
                    author = author_link.get_text(strip=True)
                    print(f"✍️ Author found: {author}")
        else:
            print("❌ Author icon not found")

        # Extract description
        print("🔍 Looking for description...")
        description = "No description"
        desc_elem = soup.find("div", class_="m-desc")
        if desc_elem:
            print("✅ Found description container")
            txt_div = desc_elem.find("div", class_="txt")
            if txt_div:
                paragraphs = txt_div.find_all("p")
                if paragraphs:
                    description = " ".join(p.get_text(strip=True) for p in paragraphs)
                    print(f"📝 Description extracted from {len(paragraphs)} paragraphs")
                else:
                    description = txt_div.get_text(strip=True)
                    print("📝 Description extracted from text div")
        else:
            print("❌ Description container not found")

        # Extract cover URL
        print("🔍 Looking for cover image...")
        cover_url = ""
        pic_div = soup.find("div", class_="pic")
        if pic_div:
            print("✅ Found picture container")
            img_tag = pic_div.find("img")
            if img_tag:
                src = img_tag.get("src")
                if isinstance(src, str):
                    cover_url = urljoin(url, src) if src.startswith("/") else src
                    print(f"🖼️ Cover URL found: {cover_url}")
            else:
                print("❌ No image tag found in picture container")
        else:
            print("❌ Picture container not found")

        print("📦 Assembling NovelMetadata object...")
        metadata = NovelMetadata(
            title=title,
            author=author,
            description=description,
            cover_url=cover_url,
            source_url=url,
            slug=slugify(title)
        )
        
        print("✅ Metadata scraping completed:")
        print(f"   Title: {metadata.title}")
        print(f"   Author: {metadata.author}")
        print(f"   Description length: {len(metadata.description)}")
        print(f"   Cover URL: {metadata.cover_url}")
        print(f"   Source URL: {metadata.source_url}")
        print(f"   Slug: {metadata.slug}")
        
        return metadata

    async def get_chapter_list(self, url: str) -> list[ChapterMetadata]:
        print(f"📚 Getting chapter list for URL: {url}")
        
        html = await self.fetch_html(url)
        print(f"📄 HTML fetched for chapter list: {'Success' if html else 'Failed'}")
        
        if not html:
            print("❌ No HTML content, returning empty chapter list")
            return []

        soup = BeautifulSoup(html, "lxml")
        print("✅ HTML parsed for chapter list")

        # Find chapter list container
        print("🔍 Looking for chapter list container...")
        chapter_list = soup.find("ul", class_="ul-list5", id="idData")
        if not chapter_list:
            print("❌ Chapter list container not found")
            return []

        print("✅ Chapter list container found")

        # Find all list items
        chapter_items = chapter_list.find_all("li")
        print(f"📖 Found {len(chapter_items)} chapter items")

        chapters: list[ChapterMetadata] = []
        
        for i, li in enumerate(chapter_items, start=1):
            print(f"🔍 Processing chapter {i}...")
            
            # Find the anchor tag within each li
            link = li.find("a", class_="con", href=True)
            if link:
                chapter_url = link.get("href")
                if isinstance(chapter_url, str):
                    # Make URL absolute if it's relative
                    if chapter_url.startswith("/"):
                        chapter_url = urljoin(url, chapter_url)
                    
                    chapter_title = link.get_text(strip=True)
                    print(f"   📝 Chapter {i}: {chapter_title}")
                    print(f"   🔗 URL: {chapter_url}")

                    chapters.append(
                        ChapterMetadata(
                            title=chapter_title,
                            url=chapter_url,
                            chapter_number=i,
                        )
                    )
                else:
                    print(f"   ❌ Invalid URL type for chapter {i}")
            else:
                print(f"   ❌ No link found for chapter {i}")

        print(f"✅ Chapter list completed: {len(chapters)} chapters found")
        return chapters

    async def scrape_chapter(self, chapter_url: str) -> str:
        print(f"📖 Scraping chapter content from: {chapter_url}")
        
        html = await self.fetch_html(chapter_url)
        print(f"📄 Chapter HTML fetched: {'Success' if html else 'Failed'}")
        
        if not html:
            error_msg = "Failed to fetch chapter content"
            print(f"❌ {error_msg}")
            return error_msg

        soup = BeautifulSoup(html, "lxml")
        print("✅ Chapter HTML parsed")

        # Extract chapter content
        print("🔍 Looking for chapter content container...")
        content_elem = soup.find("div", id="article")
        if not content_elem:
            error_msg = "Chapter content not found"
            print(f"❌ {error_msg}")
            return error_msg

        print("✅ Chapter content container found")
        print(f"📊 Initial content element type: {type(content_elem)}")

        # Extract chapter title FIRST before modifying the content
        print("🔍 Looking for chapter title...")
        title_elem = content_elem.find("h4")
        title = title_elem.get_text(strip=True) if title_elem else ""
        print(f"📝 Chapter title: {title if title else 'Not found'}")

        # Create a copy of the content element to work with
        print("🔧 Creating working copy of content...")
        working_content = BeautifulSoup(str(content_elem), 'lxml').find('div', id='article')
        if not working_content:
            print("❌ Failed to create working copy")
            return "Failed to process chapter content"
        
        print("✅ Working copy created")

        # Clean up unwanted elements from the working copy
        print("🧹 Cleaning up unwanted elements...")
        unwanted_tags = ["script", "style", "nav", "header", "footer"]
        for tag in unwanted_tags:
            elements = working_content.find_all(tag)
            print(f"   Removing {len(elements)} {tag} elements")
            for elem in elements:
                elem.decompose()
        
        print("✅ Unwanted elements removed")

        # Remove div elements except the main article div - FIXED APPROACH
        print("🧹 Removing extra div elements...")
        # Find all divs first, then process them
        all_divs = working_content.find_all('div')
        print(f"📊 Found {len(all_divs)} div elements total")
        
        divs_removed = 0
        divs_to_remove = []
        
        # First, identify which divs to remove
        for div in all_divs:
            if div.get('id') != 'article':
                divs_to_remove.append(div)
        
        print(f"📊 Identified {len(divs_to_remove)} divs to remove")
        
        # Then remove them
        for div in divs_to_remove:
            try:
                # Instead of decompose, we'll extract the content and replace the div with its contents
                div.replace_with_children()
                divs_removed += 1
            except Exception as e:
                print(f"❌ Error removing div: {e}")
                continue
        
        print(f"✅ Processed {divs_removed} extra div elements")

        # Get all paragraphs
        print("🔍 Extracting paragraphs...")
        paragraphs = working_content.find_all('p')
        print(f"📝 Found {len(paragraphs)} paragraphs")

        # Build content with title and paragraphs
        content_parts: list[str] = []
        if title:
            content_parts.extend([title, ""])  # Title with empty line
            print("✅ Added chapter title to content")

        # Add non-empty paragraphs
        print("📝 Filtering and adding paragraphs...")
        non_empty_paragraphs = 0
        for i, p in enumerate(paragraphs):
            try:
                text = p.get_text(strip=True)
                if text:
                    content_parts.append(text)
                    non_empty_paragraphs += 1
            except Exception as e:
                print(f"❌ Error processing paragraph {i}: {e}")
                continue
        
        print(f"✅ Added {non_empty_paragraphs} non-empty paragraphs to content")
        
        final_content = "\n\n".join(content_parts)
        print(f"📄 Chapter content assembled: {len(final_content)} characters")
        
        if not final_content.strip():
            print("⚠️ WARNING: Final content is empty!")
        
        return final_content