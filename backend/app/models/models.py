from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class ShijingItem(Base):
    """诗经事物模型 - 草木鸟兽虫鱼"""
    __tablename__ = "shijing_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(10), nullable=False, index=True)  # 草、木、鸟、兽、虫、鱼
    poem = Column(String(100), nullable=False, index=True)  # 所属诗篇
    source = Column(String(50), nullable=False, index=True)  # 出处（如：周南、邶风等）
    quote = Column(Text, nullable=False)  # 引用诗句
    description = Column(Text, nullable=True)  # 简要注释
    image_url = Column(String(255), nullable=True, default="")  # 图片路径
    
    # 详细释义
    modern_name = Column(String(255), nullable=True, default="")  # 今名
    taxonomy = Column(String(255), nullable=True, default="")  # 纲目属
    symbolism = Column(Text, nullable=True, default="")  # 寓意
    wiki_link = Column(String(255), nullable=True, default="")  # 百科链接

    def __repr__(self):
        return f"<ShijingItem(id={self.id}, name='{self.name}', category='{self.category}')>"


class Poem(Base):
    """诗经诗篇模型"""
    __tablename__ = "poems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, unique=True, index=True)  # 诗名
    chapter = Column(String(50), nullable=False, index=True)  # 章节（如：国风）
    section = Column(String(50), nullable=False, index=True)  # 部分（如：周南）
    content = Column(Text, nullable=False)  # 诗篇内容（JSON 数组字符串）
    full_source = Column(String(100), nullable=False)  # 完整来源（如：国风·周南·关雎）

    def __repr__(self):
        return f"<Poem(id={self.id}, title='{self.title}', chapter='{self.chapter}')>"
