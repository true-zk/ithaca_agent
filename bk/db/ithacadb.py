from typing import List, Optional, Callable, Any, Type, Dict, Union
import functools
from sqlmodel import SQLModel, select, create_engine, text, Session
from sqlalchemy.engine import Engine
from sqlalchemy import desc, asc, and_, or_
from datetime import datetime, timedelta

from ithaca.settings import DB_PATH
from ithaca.utils import get_cache_dir
from ithaca.logger import logger


class IthacaDB:
    """
    IthacaDB class, provide a unified interface to the database.
    If settings.DB_PATH is not set, use the default cache_directory/ithaca.db.
    
    _db_engine is singleton.
    """
    _db_engine: Engine = None
    _db_available: bool = False
    _check_time: datetime = None
    _check_interval: int = 60   # 60 s

    @classmethod
    def get_db_engine(cls) -> Engine:
        if cls._db_engine is None:
            db_path = DB_PATH or get_cache_dir() / "ithaca.db"
            cls._db_engine = create_engine(
                url=f"sqlite:///{db_path}",
                pool_size=300,
                max_overflow=500,
                pool_timeout=30,
                pool_pre_ping=True,
            )
            # init the database
            # before init, import all the models
            import ithaca.db.history
            try:
                SQLModel.metadata.create_all(cls._db_engine)
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
            cls._db_available = True
            cls._check_time = datetime.now()
            logger.info(f"Database initialized successfully at {db_path}")
        return cls._db_engine

    @classmethod
    def check_db_available(cls, force: bool = False) -> bool:
        if not force and cls._db_available and cls._check_time is not None:
            if datetime.now() - cls._check_time < timedelta(seconds=cls._check_interval):
                logger.debug(f"Database is available, last checked at {cls._check_time}")
                return True
        
        try:
            engine = cls.get_db_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            cls._db_available = True
            cls._check_time = datetime.now()
            logger.info(f"Database is available, refreshed at {cls._check_time}")
            return True
        except Exception as e:
            cls._db_available = False
            cls._check_time = datetime.now()
            logger.error(f"Database is not available: {e}")
            return False
    
    # CURD operations, all static methods
    @staticmethod
    def create_session() -> Session:
        return Session(IthacaDB.get_db_engine())

    @staticmethod
    def db_available_wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not IthacaDB.check_db_available():
                logger.error(f"Database is not available, cannot execute {func.__name__}")
                return None if func.__name__ != "add" else False
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Failed to execute {func.__name__}: {e}")
                return None if func.__name__ != "add" else False
        return wrapper
    
    @staticmethod
    @db_available_wrapper
    def add(data: SQLModel | List[SQLModel]) -> bool:
        if isinstance(data, SQLModel):
            data = [data]
        elif not data:
            logger.error("No data to add")
            return False
        
        with IthacaDB.create_session() as session:
            session.add_all(data)
            session.commit()
        logger.info(f"Added {len(data)} data to the database")
        return True
    
    @staticmethod
    @db_available_wrapper
    def query(model: Type[SQLModel], filters: Dict[str, Any]) -> List[SQLModel]:
        with IthacaDB.create_session() as session:
            statement = select(model)
            if filters:
                for key, value in filters.items():
                    statement = statement.where(getattr(model, key) == value)
            return session.exec(statement).all()
    
    @staticmethod
    @db_available_wrapper
    def advanced_query(
        model: Type[SQLModel],
        filters: Optional[Dict[str, Any]] = None,
        time_filters: Optional[Dict[str, Union[datetime, timedelta]]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        logical_operator: str = "and"
    ) -> List[SQLModel]:
        """
        Advanced query function, support complex SQL query conditions.
        
        Args:
            model: SQLModel type
            filters: Basic filters, format: {"field_name": value} or {"field_name": {"operator": "value"}}
            time_filters: Time filters, support:
                - {"created_at_after": datetime} - Query records after the specified time
                - {"created_at_before": datetime} - Query records before the specified time
                - {"created_at_within": timedelta} - Query records in the recent specified time period
            order_by: Sort field name
            order_desc: Whether to sort in descending order (True=descending, False=ascending)
            limit: Limit the number of returned records
            offset: Skip the number of records
            logical_operator: Logical relationship between multiple conditions ("and" or "or")
        
        Returns:
            List[SQLModel]: Query result list
            
        Examples:
            # Query the last 5 records
            IthacaDB.advanced_query(
                HistoryModel, 
                order_by="created_at", 
                order_desc=True, 
                limit=5
            )
            
            # Query the records in the last 7 days
            IthacaDB.advanced_query(
                HistoryModel,
                time_filters={"created_at_within": timedelta(days=7)},
                order_by="created_at",
                order_desc=True
            )
            
            # Query the recent records of the specified product
            IthacaDB.advanced_query(
                HistoryModel,
                filters={"product_name": "iPhone"},
                time_filters={"created_at_after": datetime(2024, 1, 1)},
                order_by="created_at",
                limit=10
            )
            
            # Complex condition query (records with score greater than 8.0 or in the last 3 days)
            IthacaDB.advanced_query(
                HistoryModel,
                filters={
                    "plan_score": {">=": 8.0}
                },
                time_filters={"created_at_within": timedelta(days=3)},
                logical_operator="or",
                order_by="plan_score",
                order_desc=True
            )
        """
        with IthacaDB.create_session() as session:
            statement = select(model)
            conditions = []
            
            # Handle basic filters
            if filters:
                for key, value in filters.items():
                    field = getattr(model, key)
                    
                    if isinstance(value, dict):
                        # Support operators: {">=": 8.0}, {"<": 100}, {"!=": "test"}, {"like": "%pattern%"}
                        for operator, op_value in value.items():
                            if operator == ">=":
                                conditions.append(field >= op_value)
                            elif operator == "<=":
                                conditions.append(field <= op_value)
                            elif operator == ">":
                                conditions.append(field > op_value)
                            elif operator == "<":
                                conditions.append(field < op_value)
                            elif operator == "!=":
                                conditions.append(field != op_value)
                            elif operator == "like":
                                conditions.append(field.like(op_value))
                            elif operator == "in":
                                conditions.append(field.in_(op_value))
                            elif operator == "not_in":
                                conditions.append(~field.in_(op_value))
                            else:
                                conditions.append(field == op_value)
                    else:
                        # Simple equal value query
                        conditions.append(field == value)
            
            # Handle time filters
            if time_filters:
                for time_key, time_value in time_filters.items():
                    if time_key.endswith("_after"):
                        field_name = time_key.replace("_after", "")
                        field = getattr(model, field_name)
                        conditions.append(field >= time_value)
                    elif time_key.endswith("_before"):
                        field_name = time_key.replace("_before", "")
                        field = getattr(model, field_name)
                        conditions.append(field <= time_value)
                    elif time_key.endswith("_within"):
                        field_name = time_key.replace("_within", "")
                        field = getattr(model, field_name)
                        cutoff_time = datetime.now() - time_value
                        conditions.append(field >= cutoff_time)
            
            # Apply conditions
            if conditions:
                if logical_operator.lower() == "or":
                    statement = statement.where(or_(*conditions))
                else:  # default to "and"
                    statement = statement.where(and_(*conditions))
            
            # Sort
            if order_by:
                field = getattr(model, order_by)
                if order_desc:
                    statement = statement.order_by(desc(field))
                else:
                    statement = statement.order_by(asc(field))
            
            # Pagination
            if offset:
                statement = statement.offset(offset)
            if limit:
                statement = statement.limit(limit)
            
            return session.exec(statement).all()
    
    @staticmethod
    @db_available_wrapper
    def update(data: SQLModel | List[SQLModel]) -> bool:
        if isinstance(data, SQLModel):
            data = [data]
        elif not data:
            logger.error("No data to update")
            return False
        
        with IthacaDB.create_session() as session:
            session.add_all(data)
            session.commit()
            for item in data:
                session.refresh(item)
        return True
    
    @staticmethod
    @db_available_wrapper
    def delete(data: SQLModel) -> bool:
        with IthacaDB.create_session() as session:
            session.delete(data)
            session.commit()
        return True