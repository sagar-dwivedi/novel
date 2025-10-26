# WebNovel Scraper

A modern web application for scraping, reading, and exporting web novels from various sources. Built with FastAPI, SQLAlchemy 2.0, and modern Python.

## ⚠️ Legal Notice

This project is for **educational and personal use only**. Users are responsible for:

- Respecting website terms of service
- Not violating copyright laws
- Not overloading servers with requests
- Using content only as permitted by law

The authors are not responsible for misuse of this software.

## 🌟 Features

- **Multi-source Scraping**: Support for multiple web novel websites (starting with LibRead)
- **Smart Metadata Extraction**: Automatically extracts novel title, author, description, and cover art
- **Chapter Management**: Selective chapter scraping with range selection
- **Web Reader**: Clean, responsive reading interface with chapter navigation
- **EPUB Export**: Export entire novels as EPUB files for offline reading
- **SEO-friendly URLs**: Uses slugs for clean, readable URLs
- **Modern Database**: SQLAlchemy 2.0 with proper relationships and type hints
- **RESTful API**: Full API support for integration with other applications

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd webnovel-scraper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   Open http://localhost:8000 in your browser

## 📖 Usage

### Adding a Novel

1. Go to the home page
2. Enter the URL of a web novel (e.g., `https://libread.com/novel/example`)
3. Click "Scrape Metadata" to extract novel information
4. The novel will be added to your library

### Scraping Chapters

1. Navigate to the novel's detail page
2. Specify the chapter range to scrape (or leave empty for all chapters)
3. Click "Scrape Chapters" to download chapter content
4. Chapters will appear in the reading list

### Reading

1. Click on any chapter from the novel detail page
2. Use the navigation buttons or chapter dropdown to move between chapters
3. Enjoy reading with the clean, distraction-free interface

### Exporting

1. From the novel detail page, click "Export as EPUB"
2. Download the generated EPUB file
3. Transfer to your favorite e-reader or reading app

## 🏗️ Project Structure

```
webnovel-scraper/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Database configuration
│   ├── scraper/
│   │   ├── base_scraper.py  # Base scraper class
│   │   ├── libread_scraper.py  # LibRead-specific scraper
│   │   └── scraper_factory.py  # Scraper factory
│   ├── utils/
│   │   └── export.py        # EPUB export functionality
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS and static files
├── requirements.txt
└── run.py
```

## 🗄️ Database Models

### Novel
- `id`: Primary key
- `title`: Novel title
- `slug`: URL-friendly identifier
- `author`: Novel author
- `description`: Novel description/synopsis
- `cover_url`: Cover image URL
- `source_url`: Original novel URL
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Chapter
- `id`: Primary key
- `title`: Chapter title
- `content`: Chapter content
- `chapter_number`: Chapter position in novel
- `novel_id`: Foreign key to Novel

## 🔌 API Endpoints

### Web Interface
- `GET /` - Home page with novel list
- `POST /scrape-metadata` - Scrape novel metadata
- `GET /novel/{slug}` - Novel detail page
- `POST /scrape-chapters` - Scrape chapters
- `GET /read/{slug}/{chapter_number}` - Chapter reader
- `GET /export/{slug}` - Export novel as EPUB


## 🛠️ Development

### Adding New Scrapers

1. Create a new scraper class in `app/scraper/`:
   ```python
   from .base_scraper import BaseScraper

   class NewSiteScraper(BaseScraper):
       async def scrape_metadata(self, url: str) -> Dict:
           # Implement metadata extraction
           pass
       
       async def get_chapter_list(self, url: str) -> List[Dict]:
           # Implement chapter list extraction
           pass
       
       async def scrape_chapter(self, chapter_url: str) -> str:
           # Implement chapter content extraction
           pass
   ```

2. Update `BaseScraper.get_scraper_for_url()` to recognize your domain
3. Add the scraper to `ScraperFactory`

### Environment Variables

Create a `.env` file for configuration:

```env
DATABASE_URL=sqlite:///./webnovels.db
DEBUG=true
```

### Running Tests

```bash
pytest tests/
```

## ⚠️ Legal Notice

This tool is intended for personal use only. Please:

- Respect website terms of service
- Don't overload servers with requests
- Only download content you have rights to access
- Support authors by purchasing official releases when available

The developers are not responsible for misuse of this software.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**Scraping fails:**
- Check if the website structure has changed
- Verify the URL is correct and accessible
- Check your internet connection

**Database errors:**
- Delete `webnovels.db` to reset the database
- Ensure SQLite write permissions

**EPUB export fails:**
- Ensure all required chapters are scraped
- Check disk space availability

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include the novel URL and error messages

---

**Happy Reading! 📚**