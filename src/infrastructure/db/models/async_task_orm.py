from src.infrastructure.db.base import db
from datetime import datetime, timezone

class AsyncTaskORM(db.Model):
    __tablename__ = 'async_tasks'

    task_id = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # 'ingredient_recognition'
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Input/Output data
    input_data = db.Column(db.JSON, nullable=True)  # images_paths, etc.
    result_data = db.Column(db.JSON, nullable=True)  # recognition result
    error_message = db.Column(db.Text, nullable=True)
    
    # Progress tracking
    progress_percentage = db.Column(db.Integer, default=0)
    current_step = db.Column(db.String(100), nullable=True)  # 'Detecting ingredients', 'Generating images', etc.
    
    def __repr__(self):
        return f"AsyncTask(id={self.task_id}, type={self.task_type}, status={self.status}, progress={self.progress_percentage}%)" 