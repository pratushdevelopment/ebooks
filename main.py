from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql.schema import ForeignKey
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, SmallInteger, desc, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql.schema import ForeignKey
from typing import List

app = FastAPI()

# Database connection
DATABASE_URL = "postgresql://postgres:1994@127.0.0.1:5555/ndl_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Models
class Book(Base):
    __tablename__ = "books"

    _id = Column(Integer, primary_key=True, index=True)
    book_title = Column(String)
    book_cover_img = Column(String)
    book_desc = Column(String)
    book_cat = Column(Integer, ForeignKey("bookscategories._id"))
    book_author = Column(Integer, ForeignKey("authors._id"))
    book_status = Column(Boolean)
    book_link = Column(String)
    book_year = Column(Integer)
    book_pages = Column(Integer)
    language_id = Column(Integer, ForeignKey("languages._id"))
    agegroup_id = Column(Integer, ForeignKey("agegroups._id"))
    book_publisher = Column(Integer, ForeignKey("authors._id"))

    category = relationship("BookCategory", back_populates="books")
    author = relationship("Author", foreign_keys=[book_author], back_populates="books_authored")
    publisher = relationship("Author", foreign_keys=[book_publisher], back_populates="books_published")
    language = relationship("Language", back_populates="books")
    agegroup = relationship("AgeGroup", back_populates="books")

class Author(Base):
    __tablename__ = "authors"

    _id = Column(Integer, primary_key=True, index=True)
    author_name = Column(String)
    author_img = Column(String)
    author_desc = Column(String)
    is_publisher = Column(Integer)

    books_authored = relationship("Book", foreign_keys=[Book.book_author], back_populates="author")
    books_published = relationship("Book", foreign_keys=[Book.book_publisher], back_populates="publisher")

class BookCategory(Base):
    __tablename__ = "bookscategories"

    _id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), nullable=False)
    description = Column(Text)
    category_img_url = Column(String(255))
    status = Column(Boolean, default=False)

    books = relationship("Book", back_populates="category")

class Language(Base):
    __tablename__ = "languages"

    _id = Column(Integer, primary_key=True, index=True)
    language = Column(String(20), nullable=False)
    lang = Column(String(10), nullable=False)
    localname = Column(String(10), nullable=False)
    status = Column(SmallInteger, nullable=False)

    books = relationship("Book", back_populates="language")

class AgeGroup(Base):
    __tablename__ = "agegroups"

    _id = Column(Integer, primary_key=True, index=True)
    agegroup = Column(String(20), nullable=False)

    books = relationship("Book", back_populates="agegroup")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    recent_books = db.query(Book).order_by(desc(Book._id)).limit(10).all()
    recommended_books = db.query(Book).order_by(func.random()).limit(10).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_books": recent_books,
        "recommended_books": recommended_books
    })

@app.get("/search")
async def search_books(request: Request, q: str, db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.book_title.ilike(f"%{q}%")).all()
    return templates.TemplateResponse("search_results.html", {"request": request, "books": books, "query": q})

@app.get("/read-book/{book_link:path}")
async def read_book(book_link: str):
    return {"message": f"Reading book from {book_link}"}

@app.get("/books")
async def list_books(request: Request, db: Session = Depends(get_db)):
    books = db.query(Book).all()
    return templates.TemplateResponse("books.html", {"request": request, "books": books})

@app.get("/book/{book_id}")
async def book_details(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book._id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse("book_details.html", {"request": request, "book": book})

@app.get("/categories")
async def list_categories(request: Request, db: Session = Depends(get_db)):
    categories = db.query(BookCategory).all()
    return templates.TemplateResponse("categories.html", {"request": request, "categories": categories})

@app.get("/authors")
async def list_authors(request: Request, db: Session = Depends(get_db)):
    authors = db.query(Author).all()
    return templates.TemplateResponse("authors.html", {"request": request, "authors": authors})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
