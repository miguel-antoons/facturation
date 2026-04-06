import jaydebeapi
import threading
import os
import time
from dotenv import dotenv_values


_db = None


class SmartAccessConnector:
    def __init__(self, db_path, ucanaccess_jars_path, idle_timeout_sec=1800, extra_params=""):
        self.db_path = db_path
        self.jars = ucanaccess_jars_path
        self.idle_timeout = idle_timeout_sec

        self.conn = None
        self.last_load_time = 0
        self.last_usage_time = 0

        self.lock = threading.Lock()

        self.driver_name = "net.ucanaccess.jdbc.UcanaccessDriver"
        self.jdbc_url = f"jdbc:ucanaccess://{self.db_path};{extra_params}"

    def _current_db_mtime(self):
        try:
            return os.path.getmtime(self.db_path)
        except OSError:
            return 0

    def _connect(self):
        return jaydebeapi.connect(self.driver_name, self.jdbc_url, ["", ""], self.jars)

    def get_connection(self):
        """
        Internal method to get/refresh connection.
        MUST be called inside a 'with self.lock:' block.
        """
        current_time = time.time()
        current_db_mtime = self._current_db_mtime()

        is_file_changed = current_db_mtime > self.last_load_time
        is_connection_stale = (current_time - self.last_usage_time) > self.idle_timeout

        if self.conn is None or is_file_changed or is_connection_stale:
            reason = "File Changed" if is_file_changed else "Connection Stale"

            if self.conn:
                print(f"Reloading DB ({reason})...")
                try:
                    self.conn.close()
                except:
                    pass
            else:
                print("Initializing DB connection...")

            self.conn = self._connect()
            self.last_load_time = current_db_mtime

        self.last_usage_time = current_time
        return self.conn

    def execute_query(self, query, params=None, fetch_one=False):
        """
        Thread-safe wrapper to execute a query.
        Handles locking, connecting, cursor management, and result fetching.
        """
        # We lock the ENTIRE operation.
        # No other user can touch the DB until this block finishes.
        with self.lock:
            conn = self.get_connection()
            curs = conn.cursor()
            try:
                if params:
                    curs.execute(query, params)
                else:
                    curs.execute(query)

                # If it's a SELECT query, fetch results
                if query.strip().upper().startswith("SELECT"):
                    return curs.fetchone() if fetch_one else curs.fetchall()
                else:
                    if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                        conn.commit()

                    # For INSERT/UPDATE, usually return None or row count
                    return None
            finally:
                curs.close()
                # We do NOT close the connection; we keep it for the next user.


def get_connection() -> SmartAccessConnector:
    global _db
    if not _db:
        db_path = dotenv_values(".env")["DB_FILE"]
        classpath = "./ucanaccess-5.1.3-uber.jar"
        _db = SmartAccessConnector(db_path, classpath, idle_timeout_sec=10080, extra_params="immediatelyReleaseResources=true")
    return _db
