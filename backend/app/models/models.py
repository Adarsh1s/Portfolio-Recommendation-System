from sqlalchemy import (
    Integer, String, Text, Numeric, Boolean, TIMESTAMP,
    ForeignKey, CheckConstraint, JSON, Date
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id:       Mapped[int]  = mapped_column(Integer, primary_key=True)
    name:          Mapped[str]  = mapped_column(String(100), nullable=False)
    email:         Mapped[str]  = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str]  = mapped_column(Text, nullable=False)
    created_at:    Mapped[str]  = mapped_column(TIMESTAMP, server_default=func.now())

    profile:    Mapped["UserProfile"]    = relationship(back_populates="user", uselist=False)
    portfolios: Mapped[list["UserPortfolio"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]]     = relationship(back_populates="user")


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    risk_profile_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_name:    Mapped[str] = mapped_column(String(50), nullable=False)
    min_score:       Mapped[int] = mapped_column(Integer, nullable=False)
    max_score:       Mapped[int] = mapped_column(Integer, nullable=False)
    description:     Mapped[str] = mapped_column(Text)

    user_profiles:    Mapped[list["UserProfile"]]    = relationship(back_populates="risk_profile")
    portfolio_models: Mapped[list["PortfolioModel"]] = relationship(back_populates="risk_profile")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    profile_id:               Mapped[int]   = mapped_column(Integer, primary_key=True)
    user_id:                  Mapped[int]   = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), unique=True)
    monthly_income:           Mapped[float] = mapped_column(Numeric(12, 2))
    monthly_expenses:         Mapped[float] = mapped_column(Numeric(12, 2))
    investment_amount:        Mapped[float] = mapped_column(Numeric(12, 2))
    investment_horizon_years: Mapped[int]   = mapped_column(Integer)
    investment_goal:          Mapped[str]   = mapped_column(String(100))
    risk_score:               Mapped[int]   = mapped_column(Integer)
    risk_profile_id:          Mapped[int]   = mapped_column(ForeignKey("risk_profiles.risk_profile_id"))
    updated_at:               Mapped[str]   = mapped_column(TIMESTAMP, server_default=func.now())

    user:         Mapped["User"]        = relationship(back_populates="profile")
    risk_profile: Mapped["RiskProfile"] = relationship(back_populates="user_profiles")


class AssetClass(Base):
    __tablename__ = "asset_classes"

    asset_class_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name:           Mapped[str] = mapped_column(String(100), nullable=False)
    description:    Mapped[str] = mapped_column(Text)

    instruments: Mapped[list["Instrument"]] = relationship(back_populates="asset_class")


class PortfolioModel(Base):
    __tablename__ = "portfolio_models"

    model_id:        Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name:      Mapped[str] = mapped_column(String(100), nullable=False)
    risk_profile_id: Mapped[int] = mapped_column(ForeignKey("risk_profiles.risk_profile_id"))
    description:     Mapped[str] = mapped_column(Text)

    risk_profile:          Mapped["RiskProfile"]             = relationship(back_populates="portfolio_models")
    portfolio_allocations: Mapped[list["PortfolioAllocation"]] = relationship(back_populates="model")
    sub_templates:         Mapped[list["SubAllocationTemplate"]] = relationship(back_populates="model")
    user_portfolios:       Mapped[list["UserPortfolio"]]      = relationship(back_populates="model")


class PortfolioAllocation(Base):
    __tablename__ = "portfolio_allocations"

    allocation_id:         Mapped[int]   = mapped_column(Integer, primary_key=True)
    model_id:              Mapped[int]   = mapped_column(ForeignKey("portfolio_models.model_id", ondelete="CASCADE"))
    asset_class_id:        Mapped[int]   = mapped_column(ForeignKey("asset_classes.asset_class_id"))
    allocation_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    model:       Mapped["PortfolioModel"] = relationship(back_populates="portfolio_allocations")
    asset_class: Mapped["AssetClass"]     = relationship()


class SubAllocationTemplate(Base):
    __tablename__ = "sub_allocation_templates"

    template_id:    Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id:       Mapped[int] = mapped_column(ForeignKey("portfolio_models.model_id", ondelete="CASCADE"))
    asset_class_id: Mapped[int] = mapped_column(ForeignKey("asset_classes.asset_class_id"))

    model:                  Mapped["PortfolioModel"]          = relationship(back_populates="sub_templates")
    asset_class:            Mapped["AssetClass"]              = relationship()
    instrument_allocations: Mapped[list["InstrumentAllocation"]] = relationship(back_populates="template")


class Instrument(Base):
    __tablename__ = "instruments"

    instrument_id:   Mapped[int]  = mapped_column(Integer, primary_key=True)
    name:            Mapped[str]  = mapped_column(String(150), nullable=False)
    ticker:          Mapped[str]  = mapped_column(String(30))
    asset_class_id:  Mapped[int]  = mapped_column(ForeignKey("asset_classes.asset_class_id"))
    instrument_type: Mapped[str]  = mapped_column(String(50))
    fund_house:      Mapped[str]  = mapped_column(String(100))
    is_active:       Mapped[bool] = mapped_column(Boolean, default=True)

    asset_class: Mapped["AssetClass"] = relationship(back_populates="instruments")
    returns:     Mapped[list["InstrumentReturn"]] = relationship(back_populates="instrument")


class InstrumentAllocation(Base):
    __tablename__ = "instrument_allocations"

    inst_allocation_id:    Mapped[int]   = mapped_column(Integer, primary_key=True)
    template_id:           Mapped[int]   = mapped_column(ForeignKey("sub_allocation_templates.template_id", ondelete="CASCADE"))
    instrument_id:         Mapped[int]   = mapped_column(ForeignKey("instruments.instrument_id"))
    allocation_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    template:   Mapped["SubAllocationTemplate"] = relationship(back_populates="instrument_allocations")
    instrument: Mapped["Instrument"]             = relationship()


class UserPortfolio(Base):
    __tablename__ = "user_portfolios"

    portfolio_id:     Mapped[int]   = mapped_column(Integer, primary_key=True)
    user_id:          Mapped[int]   = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    model_id:         Mapped[int]   = mapped_column(ForeignKey("portfolio_models.model_id"))
    total_investment: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    is_active:        Mapped[bool]  = mapped_column(Boolean, default=True)
    version:          Mapped[int]   = mapped_column(Integer, default=1)
    generated_at:     Mapped[str]   = mapped_column(TIMESTAMP, server_default=func.now())

    user:      Mapped["User"]           = relationship(back_populates="portfolios")
    model:     Mapped["PortfolioModel"] = relationship(back_populates="user_portfolios")
    positions: Mapped[list["UserPortfolioPosition"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")


class UserPortfolioPosition(Base):
    __tablename__ = "user_portfolio_positions"

    position_id:           Mapped[int]   = mapped_column(Integer, primary_key=True)
    portfolio_id:          Mapped[int]   = mapped_column(ForeignKey("user_portfolios.portfolio_id", ondelete="CASCADE"))
    instrument_id:         Mapped[int]   = mapped_column(ForeignKey("instruments.instrument_id"))
    allocation_percentage: Mapped[float] = mapped_column(Numeric(5, 2))
    allocated_amount:      Mapped[float] = mapped_column(Numeric(14, 2))

    portfolio:  Mapped["UserPortfolio"] = relationship(back_populates="positions")
    instrument: Mapped["Instrument"]    = relationship()


class InstrumentReturn(Base):
    __tablename__ = "instrument_returns"

    return_id:         Mapped[int]   = mapped_column(Integer, primary_key=True)
    instrument_id:     Mapped[int]   = mapped_column(ForeignKey("instruments.instrument_id", ondelete="CASCADE"))
    period:            Mapped[str]   = mapped_column(String(10), nullable=False)
    return_percentage: Mapped[float] = mapped_column(Numeric(6, 2))
    recorded_at:       Mapped[str]   = mapped_column(Date, server_default=func.current_date())

    instrument: Mapped["Instrument"] = relationship(back_populates="returns")


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id:     Mapped[int]  = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int]  = mapped_column(ForeignKey("users.user_id"))
    action:     Mapped[str]  = mapped_column(String(100), nullable=False)
    metadata:   Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str]  = mapped_column(TIMESTAMP, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="audit_logs")
