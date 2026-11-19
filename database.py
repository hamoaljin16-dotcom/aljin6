herefrom sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

# إنشاء قاعدة بيانات SQLite محلية
engine = create_engine('sqlite:///qureo_bot.db', echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True) # Telegram ID
    username = Column(String, nullable=True)
    subscription_active = Column(Boolean, default=False)
    daily_solves_left = Column(Integer, default=3) # 3 محاولات مجانية كبداية
    
    # علاقة مع الحسابات المرتبطة
    linked_accounts = relationship("LinkedAccount", back_populates="user")

class LinkedAccount(Base):
    __tablename__ = 'linked_accounts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    qureo_username = Column(String)
    qureo_password_encrypted = Column(String)
    
    user = relationship("User", back_populates="linked_accounts")

# إنشاء الجداول
Base.metadata.create_all(engine)
