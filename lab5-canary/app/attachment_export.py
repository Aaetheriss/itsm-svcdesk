"""Export a ticket's attachments as one archive for the customer."""
import subprocess
from pathlib import Path

EXPORT_DIR = Path("/var/lib/svcdesk/exports")


def export_attachments(ticket_id: str) -> Path:
    """Pack /data/attachments/<ticket_id> into exports/<ticket_id>.tar.gz and return the archive path."""
    archive = EXPORT_DIR / f"{ticket_id}.tar.gz"
    subprocess.run(f"tar -czf {archive} -C /data/attachments {ticket_id}", shell=True, check=True)
    return archive
