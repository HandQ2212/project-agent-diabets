"""Opt-in metadata-only demo history; never store health answers or questions."""
import logging
import os
from sqlalchemy import create_engine, text

log = logging.getLogger(__name__)

def record(event):
    if os.getenv('STORE_DEMO_HISTORY', 'false').lower() != 'true': return
    url = os.getenv('DATABASE_URL')
    if not url:
        log.warning('History enabled but DATABASE_URL is missing')
        return
    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={'connect_timeout': 3})
        with engine.begin() as connection:
            connection.execute(text('CREATE TABLE IF NOT EXISTS demo_events (id BIGINT AUTO_INCREMENT PRIMARY KEY, event VARCHAR(40) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'))
            connection.execute(text('INSERT INTO demo_events (event) VALUES (:event)'), {'event': event})
        engine.dispose()
    except Exception:
        log.exception('Failed to record demo event')
