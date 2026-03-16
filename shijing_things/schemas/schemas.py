from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal

# 分类类型
category_type = Literal['草', '木', '鸟', '兽', '虫', '鱼']
CategoryType = category_type


# ==================== ShijingItem Schemas ====================

class ShijingItemBase(BaseModel):
    """事物基础模型"""
    name: str
    category: category_type
    poem: str
    source: str
    quote: str
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    modern_name: Optional[str] = ""
    taxonomy: Optional[str] = ""
    symbolism: Optional[str] = ""
    wiki_link: Optional[str] = ""


class ShijingItemCreate(ShijingItemBase):
    """创建事物请求模型"""
    pass


class ShijingItemUpdate(BaseModel):
    """更新事物请求模型"""
    name: Optional[str] = None
    category: Optional[category_type] = None
    poem: Optional[str] = None
    source: Optional[str] = None
    quote: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    modern_name: Optional[str] = None
    taxonomy: Optional[str] = None
    symbolism: Optional[str] = None
    wiki_link: Optional[str] = None


class ShijingItemResponse(ShijingItemBase):
    """事物响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class ShijingItemList(BaseModel):
    """事物列表响应"""
    items: list[ShijingItemResponse]
    total: int
    skip: int
    limit: int


# ==================== Poem Schemas ====================

class PoemBase(BaseModel):
    """诗篇基础模型"""
    title: str
    chapter: str
    section: str
    content: str  # JSON 字符串存储列表
    full_source: str


class PoemCreate(PoemBase):
    """创建诗篇请求模型"""
    pass


class PoemUpdate(BaseModel):
    """更新诗篇请求模型"""
    title: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    content: Optional[str] = None
    full_source: Optional[str] = None


class PoemResponse(PoemBase):
    """诗篇响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class PoemList(BaseModel):
    """诗篇列表响应"""
    items: list[PoemResponse]
    total: int
    skip: int
    limit: int
