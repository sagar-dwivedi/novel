from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from markupsafe import Markup

from .database import engine
from .depends import SessionDep
from .models import Base, Chapter, Novel
from .scraper.base_scraper import BaseScraper
from .scraper.scraper_factory import ScraperFactory

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WebNovel Scraper")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# -------------------- Helper: linebreaks filter --------------------
def linebreaks(text):
    if not text:
        return ""
    paragraphs = text.split("\n\n")
    result = []
    for para in paragraphs:
        if para.strip():
            para = para.replace("\n", "<br>")
            result.append(f"<p>{para}</p>")
    return Markup("\n".join(result))


templates.env.filters["linebreaks"] = linebreaks


# -------------------- Routes --------------------


@app.get("/")
async def home(request: Request, db: SessionDep):
    novels = db.scalars(select(Novel)).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "novels": novels},
    )


@app.post("/scrape-metadata")
async def scrape_metadata(url: Annotated[str, Form()], db: SessionDep):
    try:
        website = BaseScraper.get_scraper_for_url(url)
        scraper = ScraperFactory.create_scraper(website)

        async with scraper:
            metadata = await scraper.scrape_metadata(url)

            existing_novel = db.scalar(
                select(Novel).where(Novel.source_url == metadata.source_url)
            )
            if existing_novel:
                return JSONResponse(
                    {
                        "message": "Novel already exists",
                        "novel_id": existing_novel.id,
                    }
                )

            # Save new Novel
            novel = Novel(
                title=metadata.title,
                author=metadata.author,
                description=metadata.description,
                cover_url=metadata.cover_url,
                source_url=metadata.source_url,
                slug=metadata.slug,
            )
            db.add(novel)
            db.commit()
            db.refresh(novel)

            # Save chapter metadata (no ChapterMetadata table — use Chapter)
            chapter_data = await scraper.get_chapter_list(url)
            chapters = [
                Chapter(
                    title=c.title,
                    chapter_number=c.chapter_number,
                    source_url=c.url,
                    novel_id=novel.id,
                )
                for c in chapter_data
            ]
            db.add_all(chapters)
            db.commit()

            return JSONResponse(
                {
                    "message": "Metadata scraped successfully",
                    "novel_id": novel.id,
                    "slug": metadata.slug,
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping metadata: {e}")


@app.get("/novel/{novel_slug}")
async def novel_detail(request: Request, novel_slug: str, db: SessionDep):
    novel = db.scalar(select(Novel).where(Novel.slug == novel_slug))
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    chapters = db.scalars(
        select(Chapter)
        .where(Chapter.novel_id == novel.id)
        .order_by(Chapter.chapter_number)
    ).all()

    return templates.TemplateResponse(
        "novel_detail.html",
        {"request": request, "novel": novel, "chapters": chapters},
    )


@app.post("/scrape-chapters")
async def scrape_chapters(
    db: SessionDep,
    novel_id: Annotated[int, Form()],
    start_chapter: Annotated[int, Form()] = 1,
    end_chapter: Annotated[int | None, Form()] = None,
):
    """Scrape the actual content of chapters for a given novel.

    The chapter metadata (titles, URLs, numbers) must already exist in the DB.
    """
    # 1️⃣ Validate novel
    novel = db.scalar(select(Novel).where(Novel.id == novel_id))
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    # 2️⃣ Fetch all chapters for this novel (metadata only)
    chapters_query = (
        select(Chapter)
        .where(Chapter.novel_id == novel_id)
        .order_by(Chapter.chapter_number)
    )
    all_chapters = db.scalars(chapters_query).all()

    if not all_chapters:
        raise HTTPException(status_code=400, detail="No chapter metadata found")

    # 3️⃣ Slice by start_chapter and end_chapter
    if end_chapter:
        chapters_to_scrape = all_chapters[start_chapter - 1 : end_chapter]
    else:
        chapters_to_scrape = all_chapters[start_chapter - 1 :]

    if not chapters_to_scrape:
        raise HTTPException(status_code=400, detail="No chapters in specified range")

    # 4️⃣ Initialize scraper
    website = BaseScraper.get_scraper_for_url(novel.source_url)
    scraper = ScraperFactory.create_scraper(website)

    scraped_count = 0

    try:
        async with scraper:
            for chapter in chapters_to_scrape:
                # Skip if chapter already has content
                if chapter.content:
                    continue

                if not chapter.source_url:
                    continue  # skip invalid metadata rows

                # Scrape and update content
                content = await scraper.scrape_chapter(chapter.source_url)
                if not content:
                    continue

                chapter.content = content
                scraped_count += 1

            db.commit()

        return JSONResponse(
            {
                "message": f"Successfully scraped {scraped_count} chapters",
                "scraped_count": scraped_count,
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping chapters: {str(e)}",
        )


@app.get("/read/{novel_slug}/{chapter_number}")
async def read_chapter(
    request: Request, novel_slug: str, chapter_number: int, db: SessionDep
):
    novel = db.scalar(select(Novel).where(Novel.slug == novel_slug))
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    all_chapters = db.scalars(
        select(Chapter)
        .where(Chapter.novel_id == novel.id)
        .order_by(Chapter.chapter_number)
    ).all()

    chapter = next(
        (c for c in all_chapters if c.chapter_number == chapter_number), None
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    idx = all_chapters.index(chapter)
    prev_chapter = all_chapters[idx - 1] if idx > 0 else None
    next_chapter = all_chapters[idx + 1] if idx < len(all_chapters) - 1 else None

    return templates.TemplateResponse(
        "reader.html",
        {
            "request": request,
            "novel": novel,
            "chapter": chapter,
            "prev_chapter": prev_chapter,
            "next_chapter": next_chapter,
            "all_chapters": all_chapters,
        },
    )
