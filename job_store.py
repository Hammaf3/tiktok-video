"""
Production-Ready Job Tracking System
Thread-safe with automatic cleanup and TTL
"""
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional


class JobStore:
    """
    Thread-safe job tracking system with automatic cleanup

    Features:
    - Thread-safe operations
    - Automatic job expiration (1 hour TTL)
    - Memory leak prevention
    - Status tracking with timestamps
    """

    def __init__(self, ttl_seconds: int = 3600, max_jobs: int = 1000):
        """
        Initialize job store

        Args:
            ttl_seconds: Time-to-live for jobs in seconds (default: 1 hour)
            max_jobs: Maximum number of jobs to keep in memory
        """
        self.jobs = {}
        self.lock = threading.Lock()
        self.ttl_seconds = ttl_seconds
        self.max_jobs = max_jobs

    def create_job(self, job_id: str) -> Dict:
        """
        Create a new job

        Args:
            job_id: Unique job identifier

        Returns:
            Job dictionary with initial status
        """
        with self.lock:
            now = datetime.now(timezone.utc)

            job = {
                'job_id': job_id,
                'status': 'pending',
                'progress': 0,
                'message': 'Job created',
                'created_at': now.isoformat(),
                'updated_at': now.isoformat(),
                'expires_at': (now + timedelta(seconds=self.ttl_seconds)).isoformat()
            }

            self.jobs[job_id] = job
            self._cleanup_expired_jobs()

            return job.copy()

    def update_job(self, job_id: str, status: Optional[str] = None,
                   progress: Optional[int] = None, message: Optional[str] = None,
                   **extra_fields):
        """
        Update job status

        Args:
            job_id: Job identifier
            status: New status (pending, processing, completed, error)
            progress: Progress percentage (0-100)
            message: Status message
            **extra_fields: Additional fields to add to job
        """
        with self.lock:
            if job_id not in self.jobs:
                # Create placeholder if job doesn't exist
                now = datetime.now(timezone.utc)
                self.jobs[job_id] = {
                    'job_id': job_id,
                    'status': 'error',
                    'progress': 0,
                    'message': 'Job not found or expired',
                    'created_at': now.isoformat(),
                    'updated_at': now.isoformat(),
                    'expires_at': (now + timedelta(seconds=self.ttl_seconds)).isoformat()
                }

            job = self.jobs[job_id]

            # Update fields
            if status is not None:
                job['status'] = status
            if progress is not None:
                job['progress'] = min(100, max(0, progress))
            if message is not None:
                job['message'] = message

            # Add extra fields
            for key, value in extra_fields.items():
                job[key] = value

            # Update timestamp
            job['updated_at'] = datetime.now(timezone.utc).isoformat()

    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Get job status

        Args:
            job_id: Job identifier

        Returns:
            Job dictionary or None if not found
        """
        with self.lock:
            job = self.jobs.get(job_id)

            if not job:
                return None

            # Check if job has expired
            try:
                expires_at = datetime.fromisoformat(job['expires_at'])
                now = datetime.now(timezone.utc)

                if now > expires_at:
                    # Job expired
                    job['status'] = 'error'
                    job['message'] = 'Job expired (TTL exceeded)'
                    job['progress'] = 0
            except:
                pass

            # Check for timeout (processing > 10 minutes)
            if job['status'] == 'processing':
                try:
                    updated_at = datetime.fromisoformat(job['updated_at'])
                    now = datetime.now(timezone.utc)
                    elapsed = (now - updated_at).total_seconds()

                    if elapsed > 600:  # 10 minutes
                        job['status'] = 'error'
                        job['message'] = 'Processing timeout (10 minutes exceeded)'
                        job['progress'] = 0
                except:
                    pass

            return job.copy()

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                return True
            return False

    def _cleanup_expired_jobs(self):
        """
        Remove expired jobs to prevent memory leaks
        Internal method called automatically
        """
        try:
            # Only cleanup if we're near max capacity
            if len(self.jobs) < self.max_jobs * 0.8:
                return

            now = datetime.now(timezone.utc)
            expired_jobs = []

            for job_id, job in self.jobs.items():
                try:
                    expires_at = datetime.fromisoformat(job['expires_at'])
                    if now > expires_at:
                        expired_jobs.append(job_id)
                except:
                    # Invalid timestamp - mark for deletion
                    expired_jobs.append(job_id)

            # Delete expired jobs
            for job_id in expired_jobs:
                del self.jobs[job_id]

            if expired_jobs:
                print(f"[CLEANUP] Removed {len(expired_jobs)} expired jobs")

        except Exception as e:
            print(f"[CLEANUP] Error during cleanup: {str(e)}")

    def get_stats(self) -> Dict:
        """
        Get job store statistics

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            total = len(self.jobs)
            pending = sum(1 for j in self.jobs.values() if j['status'] == 'pending')
            processing = sum(1 for j in self.jobs.values() if j['status'] == 'processing')
            completed = sum(1 for j in self.jobs.values() if j['status'] == 'completed')
            error = sum(1 for j in self.jobs.values() if j['status'] == 'error')

            return {
                'total_jobs': total,
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'error': error
            }
