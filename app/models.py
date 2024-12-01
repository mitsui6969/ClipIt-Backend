import os
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
Base = declarative_base() 

class themeTable(Base):
    __tablename__ = "theme_table"
    theme_id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    theme = Column(String)
    similarities = relationship("similarityTable", back_populates="theme")

class similarityTable(Base):
    __tablename__ = "similarity_table"
    img_id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    img_url = Column(String)
    theme_id = Column(Integer,ForeignKey("theme_table.theme_id"), index=True)
    similarity = Column(Float)
    theme = relationship("themeTable", back_populates="similarities")