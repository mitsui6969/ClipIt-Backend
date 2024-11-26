import os
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker


DB_URL = os.getenv("DB_URL")
Base = declarative_base() 
class themeTable(Base):
    __tablename__ = "theme_table"
    theme_id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    theme = Column(String)
    similarities = relationship("similarityTable", back_populates="theme")

class similarityTable(Base):
    __tablename__ = "similarity_table"
    img_id = Column(Integer, primary_key=True, index=True)
    theme_id = Column(Integer,ForeignKey("theme_table.theme_id"), index=True)
    similarity = Column(Float)
    theme = relationship("themeTable", back_populates="similarities")

engine=create_engine(DB_URL,echo=True)

Base.metadata.drop_all(bind=engine)

# テーブルを再作成
print("Creating all tables...")
Base.metadata.create_all(bind=engine)

engine=create_engine(DB_URL,echo=True)
Session = sessionmaker(bind=engine)

session = Session()
# 新しいテーマを追加
new_theme = themeTable(theme="example theme")
session.add(new_theme)
session.commit()  # これで theme_id は自動的に生成される

# 類似度データを追加（theme_id は自動生成された値を使用）
new_similarity = similarityTable(img_id=123456789, theme_id=new_theme.theme_id, similarity=2.2)
session.add(new_similarity)
session.commit()

